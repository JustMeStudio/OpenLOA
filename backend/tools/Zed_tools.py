import os
import json
import csv
import time
from ulid import ULID
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from utils.com import qprint, request_LLM_api
from utils.config import load_model_config
from globals import globals

#-----------------API KEY配置区域--------------------------------
writer_model_config = load_model_config("Zed_writer_model_config")
Zed_embedding_model_config = load_model_config("Zed_embedding_model_config")
# 测试打印一下
if writer_model_config:
    print(f"(职位过滤条件生成器)成功加载配置，正在使用模型: {writer_model_config.get('model')}")
if Zed_embedding_model_config:
    print(f"(向量数据库)成功加载配置，正在使用模型: {Zed_embedding_model_config.get('model')}")
#------------------------初始化向量数据库---------------------------
collection_name = "Zed"

# 初始化持久化客户端
qprint("正在启用Chromadb客户端......")
client = chromadb.PersistentClient(path="./chroma_db", settings=Settings())
qprint("Chromadb客户端启用成功！")
# 获取 collection
qprint("正在读取向量数据库......")
col = client.get_or_create_collection(name=collection_name)
qprint("向量数据库读取成功！")
#创建Open AI 客户端
qprint("正在创建OpenAI客户端......")
oa_client = OpenAI(
    api_key= Zed_embedding_model_config.get("api_key"), 
    base_url= Zed_embedding_model_config.get("base_url") 
)
qprint("OpenAI客户端创建成功......")    


#---------------------------------------------------------------

#API embedding
def embed_api(text:str, oa_client) -> list:
    completion = oa_client.embeddings.create(
        model= Zed_embedding_model_config.get("model"),
        input= text,
        dimensions=2048, # 指定向量维度（仅 text-embedding-v3及 text-embedding-v4支持该参数）
        encoding_format="float"
    )
    response = completion.model_dump_json()
    response_dict = json.loads(response)
    embedding = response_dict["data"][0]["embedding"]
    return (embedding)

def retrieve(query: str, k: int = 5):
    qprint("正在检索以往作品......")
    # 将 query 转换成 embedding
    query_emb = embed_api(query, oa_client)
    # 搜索最相似的 k 条记录
    results = col.query(
        query_embeddings=[query_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    # # 结果是 dict，结构为 lists
    # docs = results["documents"][0]
    # metas = results["metadatas"][0]
    # dists = results["distances"][0]
    # # 打印或返回结果
    # for doc,meta, dist in zip(docs, metas, dists):
    #     qprint(f"document: {doc}, distance: {dist:.4f}")
    return results

async def record_content_to_database(content_path: str):
    content_list = []
    if content_path.lower().endswith('.txt'):
        with open(content_path, 'r', encoding='utf‑8') as f:
            content_list = [f.read()]
    elif content_path.lower().endswith('.csv'):
        with open(content_path, newline='', encoding='utf‑8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    content_list.append(row[0])
    else:
        return {"result":"failed","failure":f"Unsupported file type: {content_path}" }
    batch_size = 5000
    ids, embeddings, docs, metas = [], [], [], []
    count = 0
    # qprint (content_list)  #debug
    for content in content_list:
        embedding = embed_api(content, oa_client)
        qprint(f"成功录入第 {count + 1} 条数据！")
        count += 1
        uid = str(ULID())
        ids.append(uid)
        embeddings.append(embedding)
        docs.append(content)
        metas.append({"type": "text"})
        if len(ids) >= batch_size:
            col.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
            ids, embeddings, docs, metas = [], [], [], []
    if ids:
        col.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
    return {"result":"succeed", "recorded_num": count}


async def create_content_using_hint(hint:str):
    retrieve_results = retrieve(hint, k=8)
    docs = retrieve_results["documents"][0]
    relative_contents = [doc for doc in docs]
    relative_demos = ""
    qprint(f"一共找到{len(relative_contents)}条案例")
    for i in range(len(relative_contents)):
        relative_demos += f"#案例{i+1}\n" + relative_contents[i] + "\n"
    prompt ="本次写作相关线索如下：\n" + hint + "\n" + "作为参考，以下是一些过往的完整作品：\n"+ relative_demos
    qprint(prompt) #debug
    content = request_LLM_api(writer_model_config, prompt, system_prompt="你会根据用户提供的本次创作的线索，仿造过往写作风格完成本次写作，注意:\n1.你的篇幅长度不要与过往作品差异过大\n2.你的语言风格一定要和以往作品非常接近！\n3.创作内容中禁止出现以往作品里或本次创作线索中没提到过的内容！\n")
    if content:
        #保存到本地
        save_path = f"{globals.PROJECT_PATH}/output.txt"
        os.makedirs(globals.PROJECT_PATH, exist_ok=True) 
        with open (save_path, "w", encoding="utf-8") as f:
            f.write(content)
        qprint(save_path)
        return {"result":"succeed", "save_path":save_path}
    else:
        return {"result":"failed", "failure":"failed to get response from LLM server"}

tool_registry = {
    "create_content_using_hint": create_content_using_hint,
    "record_content_to_database": record_content_to_database,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_content_using_hint",
            "description": "根据用户提供的线索，自动抓取用户之前相关的完整作品，并完成本次创作\n",
            "parameters": {
                "type": "object",
                "properties": {
                    "hint": {
                        "type": "string",
                        "description": "用户提供的线索（自然语言描述）"
                    }
                },
                "required": ["hint"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_content_to_database",
            "description": "将已完成的作品录入数据库，方便下次创作时自动检索到",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_path": {
                        "type": "string",
                        "description": "完整的作品文件路径，支持.txt和.csv"
                    },
                },
                "required": ["content_path"]
            }
        }
    },    
]