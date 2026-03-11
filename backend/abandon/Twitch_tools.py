import re
import os   
import requests
import json
import asyncio
import base64
import time
import random
import regex
from PIL import Image
from io import BytesIO
from openai import OpenAI
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urlparse,urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.common.exceptions import (
    TimeoutException, WebDriverException,
    NoSuchElementException, ElementClickInterceptedException,
    ElementNotInteractableException)
from globals import globals

def extract_interactive_controls(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    # 过滤各个标签
    for tag_name in ['button',"a",'textarea','select']:
        for item in soup.find_all(tag_name):
            # 将所有子标签去除，只留下文字
            for child in list(item.children):
                if not isinstance(child, str):
                    # 使用 unwrap 保留子标签中的内容（纯文本）
                    child.unwrap()
            # 获取纯文本内容 移除首尾空白
            text_content = item.get_text(strip=True)
            item.string = text_content
            # 移除无用属性
            keep_attrs = ["id","name"]
            new_attrs ={}
            for attr in keep_attrs:
                if item.get(attr):
                    new_attrs[attr] = item.get(attr)
                    break
            item.attrs = new_attrs
    # 清空 textarea 内部内容
    for ta in soup.find_all('textarea'):
        ta.clear()
    selectors = {
        'buttons': soup.find_all('button'),
        'links': soup.find_all('a'),
        'inputs': soup.find_all('input'),
        'textareas': soup.find_all('textarea'),
        'selects': soup.find_all('select'),
    }
    controls = {k: [str(tag) for tag in tags] for k, tags in selectors.items()}
    return controls

def extract_image_urls(soup, base_url):
    img_urls = []
    for img in soup.find_all('img'):
        # 优先解析响应式图片 srcset
        srcset = img.get('srcset')
        if srcset:
            # 每个 srcset 项格式如 "url 300w", 用逗号分隔
            candidates = [item.strip() for item in srcset.split(',')]
            if candidates:
                first = candidates[0]
                url_part = first.split()[0]
                full_url = urljoin(base_url, url_part)
                img_urls.append(full_url)
            continue
        # fallback：尝试 src 或 data-src
        src = img.get('src') or img.get('data-src')
        if src:
            full_url = urljoin(base_url, src)
            img_urls.append(full_url)
    # 去重但保持顺序
    return list(dict.fromkeys(img_urls))

def text_match_task(text:str, task:str):
    model_config ={
        "api_key":"sk-121a8f5dd9f24398a51351a0b8e3e7d3",
        "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model":"qwen-plus"
    }
    system_prompt = ("你是一个文本内容筛选过滤专家，能判断用户输入的文本是否与任务相关："
                    "你的输出需要基于以下格式：\n"
                    "-你的输出 **必须** 是 **标准 JSON** 格式，只输出'{'match':true,'content': <原文本中与任务相关部分的摘抄>}'或者'{'match':false}',其它输出方式都不合法！"
    )
    messages = [{"role": "system", "content":system_prompt}]
    messages.append({"role": "user", "content": f"任务是：\n{task}\n以下文本是否与上述任务相关？\n{text}"})
    client = OpenAI(api_key= model_config["api_key"], base_url= model_config["base_url"],)
    #正常识别流程
    for i in range(3):
        try:
            completion = client.chat.completions.create(
                model= model_config["model"],
                messages= messages,
                response_format= {"type": "json_object"},
            )
            result = json.loads(completion.choices[0].message.content)
            print("text_match_result:\n",result)
            return result
        except Exception as e:
            print (f"文本内容匹配过滤遇到网络问题，第{i+1}次重试中......", str(e))
    print("由于网络原因没能完成文本内容匹配过滤，直接当做不符合要求处理......")
    return {"match":False}    


#抓取页面的全部资源
def fetch_page_resources(driver_instance_name, url):
    driver = globals.WEB_DRIVERS[driver_instance_name]
    time_stamp = str(get_time_stamp())
    save_folder = f'{globals.TWITCH_WORKSPACE_PATH}/page_resources/{time_stamp}'
    os.makedirs(save_folder, exist_ok=True)
    save_html_path =f'{save_folder}/html_source_code_{time_stamp}.html'
    save_controls_path = f'{save_folder}/controls_{time_stamp}.json'
    save_image_urls_path = f'{save_folder}/image_urls_{time_stamp}.txt'
    save_text_path = f'{save_folder}/text_{time_stamp}.txt'
    try:
        driver.get(url)
        driver.implicitly_wait(10)
        html_code = driver.page_source
        #保存html源代码
        with open(save_html_path, 'w', encoding='utf-8') as f:
            f.write(html_code)
        #保存网页交互控件json
        controls = extract_interactive_controls(html_code)
        with open(save_controls_path, 'w', encoding='utf-8') as f:
            json.dump(controls, f, ensure_ascii=False, indent=2)
        soup = BeautifulSoup(html_code, 'html.parser')
        # 提取图片URLs，并保存
        img_urls = extract_image_urls(soup, url)
        with open(save_image_urls_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(img_urls))
        # 提取纯文本，并保存
        for scr in soup(["script", "style"]):
            scr.decompose()
        txt = '\n'.join(line.strip() for line in soup.get_text().splitlines() if line.strip())  
        pattern = regex.compile(r'\{(?:[^{}]++|(?R))*+\}')           #删除{...}
        txt = pattern.sub('', txt)
        pattern = re.compile(r'<style\b[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL)    #删除残留标签内容<style ...>...</style>
        txt = pattern.sub('', txt)
        with open(save_text_path, 'w', encoding='utf-8') as f:
            f.write(txt)
        #判断文本内容与任务是否相关，并抄送到待提交资源文件夹，录入待提交资源metadata
        submit_path = globals.TWITCH_SUBMIT_PATH
        os.makedirs(f"{submit_path}/text", exist_ok=True)
        task = globals.TWITHCH_TASK
        text_match_result =  text_match_task(txt, task)
        if text_match_result["match"]:
            copy_text_path = f"{submit_path}/text/text_{time_stamp}.txt"
            with open(copy_text_path, 'w', encoding='utf-8') as f:
                f.write(text_match_result["content"])
                print("✅ 已抄送1篇相关文本内容至待提交资源文件夹！")
                #录入待提交资源metadata
                globals.TWITCH_SUBMIT_METADATA.append({"file_type":"text", "local_file_path":copy_text_path, "content":text_match_result["content"] ,"url": url})
        return {
            "result": "succeed",
            "url": url,
            "text": save_text_path,
            "image_urls": save_image_urls_path,
            "html_source_code": save_html_path,
            "controls_saved": save_controls_path,
            "controls": controls,
        }
    except Exception as e:
        return {"result": "failed", "failure": str(e)}


def get_time_stamp():
    return int(time.time())	

def get_unique_save_path(local_dir, file_name):
    # 获取文件扩展名
    base_name, ext = os.path.splitext(file_name)
    counter = 1
    # 构造完整的文件路径
    save_path = f"{local_dir}/{file_name}"
    # 如果文件已存在，修改文件名
    while os.path.exists(save_path):
        # 添加数字后缀
        new_name = f"{base_name}_{counter}{ext}"
        save_path = f"{local_dir}/{new_name}"
        counter += 1
    return save_path

#利用多模态大模型理解图片，避免下载无关资源
def image_keywards_match(image_url:str, keywords:str) -> dict:
    model_config ={"api_key":"sk-121a8f5dd9f24398a51351a0b8e3e7d3",
                "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model":"qwen2-vl-2b-instruct"}
    system_prompt = ("你是一个基于图像理解的图片筛选过滤专家，能判断用户输入的图像是否与文本关键词相匹配：",
                    "你的输出需要基于以下格式：\n"
                    "-只能输出'{'match':true,'content': <你对图片真实内容的具体描述>}'或者'{'match':false}',其它输出方式都不合法！"
    )
    messages = [{"role": "system", "content":system_prompt}]
    messages.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_url}}, {"type": "text", "text": f"这张图的内容是否与{keywords}相关？"}]})
    client = OpenAI(api_key= model_config["api_key"], base_url= model_config["base_url"],)
    #svg大模型无法识别，直接当做匹配处理
    if image_url.endswith(".svg"):
        print("svg图片无法识别，直接当做不符合内容要求处理......")
        return {"match":False}
    #正常识别流程
    for i in range(3):
        try:
            completion = client.chat.completions.create(
                model= model_config["model"],
                messages= messages,
                response_format= {"type": "json_object"},
            )
            result = json.loads(completion.choices[0].message.content)
            return result
        except Exception as e:
            print (f"图像内容识别过滤遇到网络问题，第{i+1}次重试中......", str(e))
    print("由于网络原因没能完成图像识别，直接当做不符合要求处理......")
    return {"match":False}

def resolution_match(image_url: str, resolution_requirements: dict) -> dict:
    min_pixel = resolution_requirements.get("min_pixel", None)
    min_width = resolution_requirements.get("min_width", None)
    min_height = resolution_requirements.get("min_height", None)
    #svg无法处理，但是像素一般很小不能满足要求，直接丢弃
    if image_url.endswith(".svg"):
        print("svg图片无法识别，直接当做不符合像素要求处理......")
        return {"match":False}
    for _ in range(3):
        try:
            # 判断是否为 data URI
            if image_url.startswith('data:'):
                # 匹配 Base64
                match = re.match(r'data:(.*?);base64,(.*)', image_url, re.S)
                if not match:
                    raise ValueError("无效的 Base64 data URI")
                b64_data = match.group(2)
                image_data = base64.b64decode(b64_data)
                img = Image.open(BytesIO(image_data))
            else:
                # 处理 HTTP/HTTPS 链接
                response = requests.get(image_url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
            # 获取图像尺寸
            width, height = img.size
            total_pixels = width * height
            print(f'图片宽度：{width}, 图片高度：{height}, 图片像素：{total_pixels}')
            if min_pixel is not None and total_pixels < min_pixel:
                return {"match":False}
            if min_width is not None and width < min_width:
                return {"match":False}
            if min_height is not None and height < min_height:
                return {"match":False}
            return {"match":True, "size":f"{width}*{height}"}
        except Exception as e:
            print(f"图像分辨率检查时出错，重试中......: {e}")
    return {"match":False}

#根据图片url列表文件批量下载图片到指定路径
async def bulk_download_image(urls_file_path: list, filter_keywords: str, resolution_requirements: dict = {"min_pixel":20000,"min_width":None,"min_height":None}, 
                              save_folder_name: str="default", quantity_limit: int= 10, timeout: int = 10):
    save_dir = f"{globals.TWITCH_SUBMIT_PATH}/images/{save_folder_name}"
    # 确保目标目录存在
    os.makedirs(save_dir, exist_ok=True)
    try:
        with open(urls_file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        return {"result":"failed", "failure": str(e)}
    result = {
        "succeed": 0,
        "failed": 0,
        "filtered": {"total":0, "for_content":0, "for_resolution":0},
        "save_path": save_dir
    }
    for url in urls:
        #如果分辨率不满足要求，直接跳过
        resolution_match_result = resolution_match(url, resolution_requirements)
        if not resolution_match_result["match"]:
            result["filtered"]["total"]+=1
            result["filtered"]["for_resolution"]+=1
            print(f"本图片分辨率未达到要求，要求是{resolution_requirements}, 直接跳过下载")
            continue
        image_size = resolution_match_result["size"]
        #先判断图片内容是否相关，再决定是否下载
        keywords_match_result = image_keywards_match(url, filter_keywords)
        if not keywords_match_result["match"]:
            result["filtered"]["total"]+=1
            result["filtered"]["for_content"]+=1
            print(f"本图片内容不是关于'{filter_keywords}', 直接跳过下载")
            continue 
        image_content = keywords_match_result["content"]               
        #进入图片下载流程
        try:
            # 情况1：url 为base64 格式
            if url.startswith("data:image/") and ";base64," in url:
                header, b64data = url.split(";base64,", 1)
                # 从 header 中解析 MIME 类型和默认后缀
                mimetype = header[len("data:"):]
                ext = mimetype.split("/")[-1]
                if ext.lower() not in ("jpg", "jpeg", "png", "gif", "bmp", "webp","svg"):
                    ext = "png"
                file_name = f"{base64.urlsafe_b64encode(os.urandom(6)).decode()[:8]}.{ext}"
                data = base64.b64decode(b64data)
                save_path = get_unique_save_path(save_dir, file_name)
                with open(save_path, "wb") as out:
                    out.write(data)
            #情况2：普通url 
            else:            
                # 发起 HTTP GET 请求，设置 stream=True 以流方式读取内容
                response = requests.get(url, stream=True, timeout=timeout)
                response.raise_for_status()  # 若状态码非 200，则抛出异常
                # 保存文件名获取+后缀修正+截取30个字符
                parsed = urlparse(url)
                path = parsed.path  # 提取 /path/to/file.jpg
                base, ext = os.path.splitext(path)
                if not ext:
                    ext = ".jpg"
                file_name = (os.path.basename(base) + ext)[-10:]
                if file_name.split(".")[-1] not in ["jpg", "jpeg", "png", "gif", "bmp", "webp","svg"]:
                    file_name =(file_name +".jpg")[-10:]
                # 保存文件名避重
                save_path = get_unique_save_path(save_dir, file_name)
                # 写入图片内容到文件
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)
            result["succeed"]+=1
            print(f"✅ 恭喜你，共计成功下载图片{result["succeed"]}张（总目标{quantity_limit}张）！")
            #将下载到的图片资源导入待提交资源包
            globals.TWITCH_SUBMIT_METADATA.append({"file_type:":"image", 
                                                   "size":image_size, 
                                                   "content":filter_keywords+f"({image_content})", 
                                                   "local_file_path":save_path, 
                                                   "url": "base64" if url.startswith("data:image/") and ";base64," in url else url
                                                   })
        except requests.exceptions.RequestException as e:
            print(f"下载失败: {e}")
            result["failed"]+=1
        except OSError as e:
            print(f"写入文件失败: {e}")
            result["failed"]+=1
        #每次尝试下载以后，随机等待一段时间，反爬（开启图片内容检测时不需要，因为识别过程已造成延迟）
        if not filter_keywords:
            time.sleep(random.uniform(2, 5))
            print("⏳ 战术性反爬等待中......")
        #数量限制触发
        if quantity_limit :
            if result["succeed"] >= quantity_limit :     #多下载点，防止无关图片太多
                break
    return result

# #启动浏览器，创建web driver实例
# async def open_browser(driver_instance_name: str = "driver_1", browser_type: str = "chrome", headless: bool = False ):
#     name = browser_type.strip().lower()
#     try:
#         if name == "chrome":
#             from selenium.webdriver.chrome.options import Options
#             options = Options()
#             options.add_experimental_option('excludeSwitches', ['enable-logging'])
#             options.add_argument('--log-level=3')
#             options.add_argument('--disable-logging')     
#             options.add_argument('--ignore-certificate-errors')
#             options.add_argument('--ignore-ssl-errors')  
#             if headless:
#                 options.add_argument("--headless")
#             driver = webdriver.Chrome(service=ChromeService(), options=options)
#         elif name == "firefox":
#             from selenium.webdriver.firefox.options import Options
#             options = Options()
#             if headless:
#                 options.add_argument("-headless")
#             driver = webdriver.Firefox(service=FirefoxService(), options=options)
#         elif name == "edge":
#             from selenium.webdriver.edge.service import Service as EdgeService
#             from selenium.webdriver.edge.options import Options
#             options = Options()
#             if headless:
#                 options.add_argument("headless")
#             driver = webdriver.Edge(service=EdgeService(), options=options)
#         else:
#             raise ValueError(f"Unsupported browser: {browser_type}")
#         # 基本设置
#         driver.maximize_window()
#         WEB_DRIVERS[driver_instance_name] = driver
#         response = { "result": "succeed", "driver_instance_name": driver_instance_name ,}
#     except (WebDriverException, ValueError) as e:
#         response = {"result": "failed", "failure":str(e)}
#     return response

# #从浏览器打开url，并获取页面的全部信息存储到本地
# async def navigate_to_url(driver_instance_name, url, timeout=10):
#     driver = WEB_DRIVERS[driver_instance_name]
#     try:
#         driver.get(url)
#         WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
#     except TimeoutException as e:
#         return { "result": "failed", "failure": f"Timeout waiting for document.readyState to be complete" }
#     except WebDriverException as e:
#         return { "result": "failed", "failure": f"WebDriver error" }
#     except KeyError as e:
#         return { "result": "failed", "failure": f"Driver instance not opened: {driver_instance_name}" }
#     #成功跳转到url后即抓取网页资源备用
#     fetch_result = fetch_page_resources(driver_instance_name, url)
#     if fetch_result["result"] == "succeed":
#         return { "result": "succeed", "driver_instance_name": driver_instance_name, "url": url, "resources_on_this_page": fetch_result}
#     else:
#         return { "result": "successfully navigated but failed to fetch resources on this page","failure": fetch_result["failure"], "solution":"try to refresh this page" }

async def open_browser_and_navigate_to_url(url: str, driver_instance_name: str = "driver_1", browser_type: str = "chrome", headless: bool = True, timeout:int=10):
    name = browser_type.strip().lower()
    try:
        if name == "chrome":
            from selenium.webdriver.chrome.options import Options
            options = Options()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument('--log-level=3')
            options.add_argument('--disable-logging')     
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')  
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Chrome(service=ChromeService(), options=options)
        elif name == "firefox":
            from selenium.webdriver.firefox.options import Options
            options = Options()
            if headless:
                options.add_argument("-headless")
            driver = webdriver.Firefox(service=FirefoxService(), options=options)
        elif name == "edge":
            from selenium.webdriver.edge.service import Service as EdgeService
            from selenium.webdriver.edge.options import Options
            options = Options()
            if headless:
                options.add_argument("headless")
            driver = webdriver.Edge(service=EdgeService(), options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser_type}")
        # 基本设置
        driver.maximize_window()
        globals.WEB_DRIVERS[driver_instance_name] = driver
        #导航到指定url
        try:
            driver.get(url)
            WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except TimeoutException as e:
            return { "result": "failed to navigate", "failure": f"Timeout waiting for document.readyState to be complete" }
        except WebDriverException as e:
            return { "result": "failed to navigate", "failure": f"WebDriver error" }
        except KeyError as e:
            return { "result": "failed to navigate", "failure": f"Driver instance not opened: {driver_instance_name}" }
        #成功跳转到url后即抓取网页资源备用
        fetch_result = fetch_page_resources(driver_instance_name, url)
        if fetch_result["result"] == "succeed":
            return { "result": "succeed", "driver_instance_name": driver_instance_name, "url": url, "resources_on_this_page": fetch_result}
        else:
            return { "result": "successfully navigated but failed to fetch resources on this page","failure": fetch_result["failure"], "solution":"try to refresh this page" }
    except (WebDriverException, ValueError) as e:
        return {"result": "failed to open the browser", "failure":str(e)}

#操作页面，输入，拉选或者点击
async def operate_on_page(driver_instance_name, selector_key, selector_value, action_type, action_value=None, timeout=10):
    driver = globals.WEB_DRIVERS[driver_instance_name]
    # 构建 selector
    try:
        if selector_key == 'id':
            selector = (By.ID, selector_value)
        elif selector_key == 'name':
            selector = (By.NAME, selector_value)
        elif selector_key == 'href':
            selector = (By.XPATH, f"//a[@href='{selector_value}']")
        elif selector_key == 'type':
            selector = (By.XPATH, f"//input[@type='{selector_value}']")
        elif selector_key == 'text':
            selector = (By.XPATH, f"//*[normalize-space(text())='{selector_value}']")
        else:
            raise ValueError(f"Unsupported selector_key: {selector_key}")
    except ValueError as e:
        return {"result": "failed", "failure": str(e)}
    try:
        # 确认控件存在
        elem = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(selector)
        )
        if action_type == 'click':
            # 如果被遮挡，尝试滚动和 JS click
            try:
                elem.click()
            except (ElementClickInterceptedException, ElementNotInteractableException):
                driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                try:
                    elem.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                    except Exception as e:
                        return {"result": "failed", "failure": f"Tried to scroll and use JS click but finally failed: {e}"}
            # 切换到最新新标签页
            driver.switch_to.window(driver.window_handles[-1])
            new_page_url = driver.current_url
            fetch_result = fetch_page_resources(driver_instance_name, new_page_url)
            if fetch_result["result"] == "succeed": 
                return {"result": "succeed", "resources_on_new_page_after_click": fetch_result}
            else :       
                return {"result": "succeed to operate but failed to fetch resources on the new page after click", "solution":"try to refresh this page"}
        # 输入
        elif action_type == 'input':
            elem.clear()
            elem.send_keys(action_value or "")
            return {"result": "succeed", "driver_instance_name": driver_instance_name,"selector_key": selector_key, "selector_value": selector_value,"action_type": action_type}
        # 拉选
        elif action_type == 'select':
            sel = Select(elem)
            sel.select_by_visible_text(action_value)
            return {"result": "succeed", "driver_instance_name": driver_instance_name,"selector_key": selector_key, "selector_value": selector_value,"action_type": action_type}
        #操作类型错误
        elif action_type not in ['click']:
            raise ValueError(f"Unsupported action_type: {action_type}")
    except TimeoutException as e:
        return {"result": "failed", "failure": f"Timeout waiting for presence of element located", "cause":"1.network 2.selector value not found on this page"}
    except NoSuchElementException as e:
        return {"result": "failed", "failure": f"Element not found on this page"}
    except WebDriverException as e:
        return {"result": "failed", "failure": f"WebDriver error"}
    except ValueError as e:
        return {"result": "failed", "failure": str(e)}


# 注册工具表
tool_registry = {
    "open_browser_and_navigate_to_url":open_browser_and_navigate_to_url,
    "operate_on_page": operate_on_page,
    "bulk_download_image": bulk_download_image,
    # "refresh_page": refresh_page
    # "close_browser": 
}

# 注册工具详情
tools = [
    {
        "type": "function",
        "function": {
            "name": "open_browser_and_navigate_to_url",
            "description": "打开浏览器并导航到指定的 URL（支持 Chrome、Firefox、Edge），同时在导航成功后尝试抓取当前页面的资源。\n"
                            "注意：\n"
                            "1.返回内容的'controls'字段中记录了该页面所有可交互控件信息\n"
                            "2.严禁读取html_source_code.html或image_urls.txt内容，否则会造成上下文过长从而阻塞进程！",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "目标网页的完整URL（一定要补全http或https前缀）"
                    },
                    "driver_instance_name": {
                        "type": "string",
                        "description": "用于标识WebDriver实例的唯一名称（用于同时管理多个浏览器窗口）",
                        "default": "driver_1"
                    },
                    "browser_type": {
                        "type": "string",
                        "description": "浏览器类型，可选值为 'chrome'、'firefox' 或 'edge'",
                        "default": "chrome"
                    },
                    "headless": {
                        "type": "boolean",
                        "description": "是否以无头模式运行浏览器",
                        "default": True
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "等待页面加载完成的超时时间（秒）",
                        "default": 10
                    }
                },
                "required": ["url"]
            }
        }
    },    
    {
        "type": "function",
        "function": {
            "name": "operate_on_page",
            "description": "在指定WebDriver实例中查找交互控件，并执行点击、输入或选择操作。如果操作以后发生页面跳转，会自动抓取新页面的资源。\n"
                            "注意：\n"
                            "1.返回内容的'controls'字段中记录了该页面所有可交互控件信息\n"
                            "2.严禁读取html_source_code.html或image_urls.txt内容，否则会造成上下文过长从而阻塞进程！",
            "parameters": {
            "type": "object",
            "properties": {
                "driver_instance_name": {
                "type": "string",
                "description": "要使用的WebDriver实例名称，用于从全局WEB_DRIVERS中提取对应 driver"
                },
                "selector_key": {
                "type": "string",
                "description": "控件属性名: 'id', 'name', 'href', 'type', 或 'text'（纯文本内容）\n须知：执行选择前请首先从'controls'字段内容中查看相应控件的唯一识别属性！"
                },
                "selector_value": {
                "type": "string",
                "description": "控件属性值（'text'属性支持模糊匹配，部分关键文本内容即可）"
                },
                "action_type": {
                "type": "string",
                "description": "操作类型: 'click', 'input', 或 'select'"
                },
                "action_value": {
                "type": "string",
                "description": "用于输入或选择操作的值（click操作时可忽略）",
                "default": None
                },
                "timeout": {
                "type": "integer",
                "description": "等待控件加载的最大时间（秒）",
                "default": 10
                }
            },
            "required": ["driver_instance_name", "selector_key", "selector_value", "action_type"]
            }
        }
    },    
    {
        "type": "function",
        "function": {
            "name": "bulk_download_image",
            "description": "读取存有图片URL列表的本地文件，将文件里URL列表中的相应图片资源下载到本地的指定目录下（支持 base64 格式和普通 HTTP URL）。",
            "parameters": {
            "type": "object",
            "properties": {
                "urls_file_path": {
                "type": "string",
                "description": "包含图片URL列表的本地文件路径，每行一个URL（可以是 base64 或 HTTP 链接）"
                },
                "filter_keywords": {
                "type": "string",
                "description": "所需要的图片内容描述，用于视觉大模型理解图片并跳过无关图片下载",
                },
                "resolution_requirements":{
                "type": "object",
                "description": "所需要的图片像素，宽度和高度要求，用于跳过下载不符合要求的图片",
                "properties":{
                    "min_pixel":{
                    "type": "integer",
                    "description": "最小像素总数要求（宽×高）"
                    },
                    "min_width":{
                    "type": "integer",
                    "description": "最小宽度要求"
                    },
                    "min_height":{
                    "type": "integer",
                    "description": "最小高度要求"
                    },
                "default": {"min_pixel":20000,"min_width":None,"min_height":None}
                }
                },
                "save_folder_name": {
                "type": "string",
                "description": "本地保存图片的目标文件夹名",
                "default": "default"
                },
                "quantity_limit": {
                "type": "integer",
                "description": "下载的图片数量上限（只计入成功下载的图片数量）",
                "default": 10
                },
                "timeout": {
                "type": "integer",
                "description": "HTTP请求的超时时间（秒）",
                "default": 10
                }
            },
            "required": ["urls_file_path", "filter_keywords"]
            }
        }
    }
]

async def main():
    result = await open_browser_and_navigate_to_url("https://www.baidu.com/")
    print (result)
    result = await operate_on_page("driver_1", 'name', "wd", "input", action_value="哈士奇")
    print (result)
    result = await operate_on_page("driver_1", 'id', "su", "click")
    print (result)
    result = await bulk_download_image("./Twitch_download/image_urls.txt")
    print (result)
    print("等待 5 秒中...")
    await asyncio.sleep(5)
    print("等待结束，关闭浏览器")

# #debug
if __name__ == '__main__':
    asyncio.run(main())