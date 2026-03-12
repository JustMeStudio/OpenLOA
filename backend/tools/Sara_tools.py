import time
import os
import json
import random
import copy
import asyncio
import docx
import fitz  # PyMuPDF
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException,StaleElementReferenceException,ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from utils.com import request_LLM_api, qprint
from utils.config import load_model_config
from globals import globals



#--------------------------------------API KEY 配置-----------------------------------------------
filter_generate_model_config = load_model_config("Sara_job_filter_generate_model_config")
# 测试打印一下
if filter_generate_model_config:
    print(f"(职位过滤条件生成器)成功加载配置，正在使用模型: {filter_generate_model_config.get('model')}")

########################################## BOSS直聘  ##########################################
city_code_bosszhipin = {
"澳门":"101330100", "阿拉尔":"101131700", "鞍山":"101070300", "安顺":"101260300", "安阳":"101180200", "阿里地区":"101140700", "安庆":"101220600", "安康":"101110700", "阿拉善盟":"101081200", "阿克苏地区":"101131000", "阿坝藏族羌族自治州":"101271900", "阿勒泰地区":"101131500", "白杨市":"101132700", "北京":"101010100", "白沙黎族自治县":"101311400", "包头":"101080200", "北屯市":"101132100", "保亭黎族苗族自治县":"101311800", "宝鸡":"101110900", "蚌埠":"101220200", "白银":"101161000", "保山":"101290300", "本溪":"101070500", "毕节":"101260500", "北海":"101301300", "白山":"101060800", "保定":"101090200", "白城":"101060500", "巴彦淖尔":"101080800", "百色":"101301000", "博尔塔拉蒙古自治州":"101130500", "巴音郭楞蒙古自治州":"101130400", "亳州":"101220900", "滨州":"101121100", "巴中":"101270900", "长春":"101060100", "长沙":"101250100", "成都":"101270100", "重庆":"101040100", "昌都":"101140300", "昌江黎族自治县":"101311500", "赤峰":"101080500", "长治":"101100500", "澄迈":"101311200", "常州":"101191100", "常德":"101250600", "承德":"101090400", "沧州":"101090700", "楚雄彝族自治州":"101291700", "滁州":"101221000", "郴州":"101250500", "昌吉回族自治州":"101130300", "朝阳":"101071200", "崇左":"101300200", "池州":"101221500", "潮州":"101281500", "大连":"101070200", "大同":"101100200", "东营":"101121200", "德阳":"101271700", "大庆":"101050800", "丹东":"101070600", "儋州":"101310400", "定安":"101311000", "东方":"101310900", "定西":"101160200", "大兴安岭地区":"101051300", "大理白族自治州":"101291600", "德州":"101120400", "德宏傣族景颇族自治州":"101291300", "达州":"101270600", "迪庆藏族自治州":"101291500", "东莞":"101281600", "东沙群岛":"101282200", "鄂尔多斯":"101080600", "鄂州":"101200300", "恩施土家族苗族自治州":"101201300", "福州":"101230100", "抚顺":"101070400", "佛山":"101280800", "防城港":"101301400", "阜新":"101070900", "抚州":"101240400", "阜阳":"101220800", "贵阳":"101260100", "广州":"101280100", "桂林":"101300500", "固原":"101170400", "果洛藏族自治州":"101150600", "赣州":"101240700", "广元":"101271800", "贵港":"101300800", "甘南藏族自治州":"101161400", "广安":"101270800", "甘孜藏族自治州":"101272100", "胡杨河市":"101132600", "哈尔滨":"101050100", "呼和浩特":"101080100", "杭州":"101210100", "合肥":"101220100", "海东":"101150200", "黄石":"101200600", "海北藏族自治州":"101150300", "鹤岗":"101051100", "邯郸":"101091000", "黄南藏族自治州":"101150400", "淮南":"101220400", "衡阳":"101250400", "海南藏族自治州":"101150500", "湖州":"101210200", "海口":"101310100", "鹤壁":"101181200", "淮北":"101221100", "呼伦贝尔":"101080700", "汉中":"101110800", "海西蒙古族藏族自治州":"101150800", "淮安":"101190900", "黄山":"101221600", "哈密":"101130900", "黄冈":"101200500", "红河哈尼族彝族自治州":"101291200", "黑河":"101050600", "衡水":"101090800", "惠州":"101280300", "贺州":"101300700", "怀化":"101251200", "河池":"101301200", "葫芦岛":"101071400", "河源":"101281200", "和田地区":"101131300", "菏泽":"101121000", "济南":"101120100", "吉林":"101060200", "嘉峪关":"101161200", "景德镇":"101240800", "鸡西":"101051000", "金昌":"101160600", "嘉兴":"101210300", "九江":"101240200", "晋城":"101100600", "锦州":"101070700", "晋中":"101100400", "荆门":"101201200", "金华":"101210900", "江门":"101281100", "佳木斯":"101050400", "焦作":"101181100", "济宁":"101120700", "吉安":"101240600", "酒泉":"101160800", "荆州":"101200800", "济源":"101181800", "揭阳":"101281900", "昆明":"101290100", "开封":"101180800", "可克达拉市":"101132200", "昆玉市":"101132300", "克拉玛依":"101130200", "克孜勒苏柯尔克孜自治州":"101131100", "喀什地区":"101131200", "拉萨":"101140100", "兰州":"101160100", "六盘水":"101260600", "柳州":"101300300", "洛阳":"101180900", "辽源":"101060600", "林芝":"101140400", "泸州":"101271000", "丽江":"101290900", "连云港":"101191000", "龙岩":"101230700", "临沧":"101290800", "辽阳":"101071000", "廊坊":"101090600", "临汾":"101100700", "乐山":"101271400", "吕梁":"101101100", "漯河":"101181500", "丽水":"101210800", "乐东黎族自治县":"101311600", "陇南":"101161100", "临高":"101311300", "临沂":"101120900", "临夏回族自治州":"101161300", "六安":"101221400", "娄底":"101250800", "来宾":"101300400", "陵水黎族自治县":"101311700", "聊城":"101121700", "凉山彝族自治州":"101272000", "马鞍山":"101220500", "绵阳":"101270400", "茂名":"101282000", "牡丹江":"101050300", "眉山":"101271500", "梅州":"101280400", "南京":"101190100", "南昌":"101240100", "南宁":"101300100", "宁波":"101210400", "那曲":"101140600", "南通":"101190500", "南平":"101230900", "宁德":"101230300", "内江":"101271200", "南充":"101270500", "南阳":"101180700", "怒江傈僳族自治州":"101291400", "莆田":"101230400", "萍乡":"101240900", "攀枝花":"101270200", "平顶山":"101180500", "普洱":"101290500", "平凉":"101160300", "濮阳":"101181300", "盘锦":"101071300", "齐齐哈尔":"101050200", "青岛":"101120200", "曲靖":"101290200", "秦皇岛":"101091100", "泉州":"101230500", "黔西南布依族苗族自治州":"101260900", "钦州":"101301100", "衢州":"101211000", "黔东南苗族侗族自治州":"101260700", "七台河":"101050900", "黔南布依族苗族自治州":"101260800", "庆阳":"101160400", "潜江":"101201500", "琼海":"101310600", "琼中黎族苗族自治县":"101311900", "清远":"101281300", "日喀则":"101140200", "日照":"101121500", "上海":"101020100", "沈阳":"101070100", "石家庄":"101090100", "石嘴山":"101170200", "韶关":"101280200", "四平":"101060300", "十堰":"101201000", "深圳":"101280600", "三明":"101230800", "双鸭山":"101051200", "石河子":"101131600", "山南":"101140500", "苏州":"101190400", "邵阳":"101250900", "汕头":"101280500", "朔州":"101100900", "双河市":"101132400", "绍兴":"101210500", "三亚":"101310200", "松原":"101060700", "三沙":"101310300", "遂宁":"101270700", "商洛":"101110600", "上饶":"101240300", "绥化":"101050500", "三门峡":"101181700", "随州":"101201100", "宿州":"101220700", "宿迁":"101191300", "汕尾":"101282100", "商丘":"101181000", "神农架":"101201700", "台湾":"101341100", "天津":"101030100", "太原":"101100100", "唐山":"101090500", "铜川":"101111000", "通化":"101060400", "通辽":"101080400", "天水":"101160900", "铜仁":"101260400", "铜陵":"101221200", "泰安":"101120800", "吐鲁番":"101130800", "台州":"101210600", "铁岭":"101071100", "泰州":"101191200", "天门":"101201600", "屯昌":"101311100", "塔城地区":"101131400", "铁门关":"101132000", "图木舒克":"101131800", "武汉":"101200100", "芜湖":"101220300", "无锡":"101190200", "乌海":"101080300", "吴忠":"101170300", "温州":"101210700", "梧州":"101300600", "渭南":"101110500", "武威":"101160500", "潍坊":"101120600", "乌鲁木齐":"101130100", "乌兰察布":"101080900", "威海":"101121300", "文山壮族苗族自治州":"101291100", "万宁":"101310800", "文昌":"101310700", "五指山":"101310500", "五家渠":"101131900", "新星市":"101132500", "香港":"101320300", "西安":"101110100", "西宁":"101150100", "厦门":"101230200", "徐州":"101190800", "湘潭":"101250200", "咸阳":"101110200", "邢台":"101090900", "襄阳":"101200200", "新余":"101241000", "新乡":"101180300", "孝感":"101200400", "忻州":"101101000", "兴安盟":"101081100", "许昌":"101180400", "锡林郭勒盟":"101081000", "咸宁":"101200700", "西双版纳傣族自治州":"101291000", "湘西土家族苗族自治州":"101251400", "信阳":"101180600", "宣城":"101221300", "仙桃":"101201400", "银川":"101170100", "阳泉":"101100300", "玉溪":"101290400", "宜昌":"101200900", "延安":"101110300", "烟台":"101120500", "鹰潭":"101241100", "岳阳":"101251000", "伊春":"101050700", "玉树藏族自治州":"101150700", "营口":"101070800", "运城":"101100800", "榆林":"101110400", "延边朝鲜族自治州":"101060900", "宜春":"101240500", "益阳":"101250700", "玉林":"101300900", "盐城":"101190700", "扬州":"101190600", "永州":"101251300", "宜宾":"101271100", "阳江":"101281800", "雅安":"101271600", "伊犁哈萨克自治州":"101130600", "云浮":"101281400", "郑州":"101180100", "株洲":"101250300", "自贡":"101270300", "淄博":"101120300", "遵义":"101260200", "枣庄":"101121400", "珠海":"101280700", "中卫":"101170500", "昭通":"101290700", "漳州":"101230600", "张家口":"101090300", "张掖":"101160700", "张家界":"101251100", "湛江":"101281000", "舟山":"101211100", "肇庆":"101280900", "镇江":"101190300", "周口":"101181400", "驻马店":"101181600", "资阳":"101271300", "中山":"101281700",
}
industry_code_bosszhipin = {
"互联网":"100020", "电子商务":"100001", "计算机软件":"100021", "生活服务(O2O)":"100007", "企业服务":"100015", "医疗健康":"100006", "游戏":"100002", "社交网络与媒体":"100003", "人工智能":"100028", "云计算":"100029", "在线教育":"100012", "计算机服务":"100023", "大数据":"100005", "广告营销":"100004", "物联网":"100030", "新零售":"100017", "信息安全":"100016", "半导体/芯片":"101405", "电子/硬件开发":"101406", "通信/网络设备":"101402", "智能硬件/消费电子":"101401", "运营商/增值服务":"101403", "计算机硬件":"101404", "电子/半导体/集成电路":"101407", "餐饮":"101101", "美容":"101111", "美发":"101112", "酒店/民宿":"101102", "休闲/娱乐":"101107", "运动/健身":"101113", "保健/养生":"101114", "家政服务":"101109", "旅游/景区":"101103", "婚庆/摄影":"101105", "宠物服务":"101110", "回收/维修":"101108", "美容/美发":"101104", "其他生活服务":"101106", "批发/零售":"101011", "进出口贸易":"101012", "食品/饮料/烟酒":"101001", "服装/纺织":"101003", "家具/家居":"101009", "家用电器":"101010", "日化":"101002", "珠宝/首饰":"101006", "家具/家电/家居":"101004", "其他消费品":"101013", "装修装饰":"100704", "房屋建筑工程":"100708", "土木工程":"100709", "机电工程":"100710", "物业管理":"100707", "房地产中介/租赁":"100706", "建筑材料":"100705", "房地产开发经营":"100701", "建筑设计":"100703", "建筑工程咨询服务":"100711", "土地与公共设施管理":"100712", "工程施工":"100702", "培训/辅导机构":"100303", "职业培训":"100305", "学前教育":"100301", "学校/学历教育":"100302", "学术/科研":"100304", "文化艺术/娱乐":"100104", "体育":"100105", "广告/公关/会展":"100101", "广播/影视":"100103", "新闻/出版":"100102", "通用设备":"100906", "专用设备":"100907", "电气机械/器材":"100908", "金属制品":"100909", "非金属矿物制品":"100910", "橡胶/塑料制品":"100911", "化学原料/化学制品":"100912", "仪器仪表":"100913", "自动化设备":"100914", "印刷/包装/造纸":"100904", "铁路/船舶/航空/航天制造":"100905", "计算机/通信/其他电子设备":"100915", "新材料":"100916", "机械设备/机电/重工":"100901", "仪器仪表/工业自动化":"100902", "原材料及加工/模具":"100903", "其他制造业":"100917", "咨询":"100711", "财务/审计/税务":"100605", "人力资源服务":"100604", "法律":"100602", "检测/认证/知识产权":"100609", "翻译":"100603", "其他专业服务":"100608", "医疗服务":"100402", "医美服务":"100404", "医疗器械":"100403", "IVD":"100405", "生物/制药":"100401", "医药批发零售":"100406", "医疗研发外包":"100407", "新能源汽车":"100804", "汽车智能网联":"100805", "汽车经销商":"100806", "汽车后市场":"100807", "汽车研发/制造":"100801", "汽车零部件":"100802", "摩托车/自行车制造":"100808", "4S店/后市场":"100803", "即时配送":"100505", "快递":"100506", "公路物流":"100507", "同城货运":"100508", "跨境物流":"100509", "装卸搬运和仓储业":"100510", "客运服务":"100511", "港口/铁路/公路/机场":"100512", "交通/运输":"100501", "物流/仓储":"100502", "光伏":"101208", "储能":"101209", "动力电池":"101210", "风电":"101211", "其他新能源":"101212", "环保":"101207", "化工":"101202", "电力/热力/燃气/水利":"101205", "石油/石化":"101201", "矿产/地质":"101203", "采掘/冶炼":"101204", "新能源":"100804", "互联网金融":"100206", "银行":"100201", "投资/融资":"100207", "证券/期货":"100203", "基金":"100204", "保险":"100202", "租赁/拍卖/典当/担保":"100208", "信托":"100205", "财富管理":"100209", "其他金融业":"100210", "农/林/牧/渔":"101303", "非盈利机构":"101302", "政府/公共事业":"101301", "其他行业":"101304",
}
job_type_code_bosszhipin = {
"全职":"1901", "兼职":"1903"
}
salary_code_bosszhipin={
"3K以下":"402","3-5K":"403","5-10K":"404","10-20K":"405","20-50k":"406","50K以上":"407"
}
experience_code_bosszhipin = {
"在校生":"108", "应届生":"102", "经验不限":"101", "1年以内":"103", "1-3年":"104", "3-5年":"105", "5-10年":"106", "10年以上":"107",
}
degree_code_bosszhipin ={
"初中及以下":"209", "中专/中技":"208", "高中":"206", "大专":"202", "本科":"203", "硕士":"204", "博士":"205",
}
scale_code_bosszhipin ={
"0-20人":"301", "20-99人":"302", "100-499人":"303", "500-999人":"304", "1000-9999人":"305", "10000人以上":"306",
}

city_math_bosszhipin = {
    "ABCDE":[ "澳门", "阿拉尔", "鞍山", "安顺", "安阳", "阿里地区", "安庆", "安康", "阿拉善盟", "阿克苏地区", "阿坝藏族羌族自治州", "阿勒泰地区", "白杨市", "北京", "白沙黎族自治县", "包头", "北屯市", "保亭黎族苗族自治县", "宝鸡", "蚌埠", "白银", "保山", "本溪", "毕节", "北海", "白山", "保定", "白城", "巴彦淖尔", "百色", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州", "亳州", "滨州", "巴中", "长春", "长沙", "成都", "重庆", "昌都", "昌江黎族自治县", "赤峰", "长治", "澄迈", "常州", "常德", "承德", "沧州", "楚雄彝族自治州", "滁州", "郴州", "昌吉回族自治州", "朝阳", "崇左", "池州", "潮州", "大连", "大同", "东营", "德阳", "大庆", "丹东", "儋州", "定安", "东方", "定西", "大兴安岭地区", "大理白族自治州", "德州", "德宏傣族景颇族自治州", "达州", "迪庆藏族自治州", "东莞", "东沙群岛", "鄂尔多斯", "鄂州", "恩施土家族苗族自治州" ],
    "FGHJ":[ "福州", "抚顺", "佛山", "防城港", "阜新", "抚州", "阜阳", "贵阳", "广州", "桂林", "固原", "果洛藏族自治州", "赣州", "广元", "贵港", "甘南藏族自治州", "广安", "甘孜藏族自治州", "胡杨河市", "哈尔滨", "呼和浩特", "杭州", "合肥", "海东", "黄石", "海北藏族自治州", "鹤岗", "邯郸", "黄南藏族自治州", "淮南", "衡阳", "海南藏族自治州", "湖州", "海口", "鹤壁", "淮北", "呼伦贝尔", "汉中", "海西蒙古族藏族自治州", "淮安", "黄山", "哈密", "黄冈", "红河哈尼族彝族自治州", "黑河", "衡水", "惠州", "贺州", "怀化", "河池", "葫芦岛", "河源", "和田地区", "菏泽", "济南", "吉林", "嘉峪关", "景德镇", "鸡西", "金昌", "嘉兴", "九江", "晋城", "锦州", "晋中", "荆门", "金华", "江门", "佳木斯", "焦作", "济宁", "吉安", "酒泉", "荆州", "济源", "揭阳" ],
    "KLMN" : [ "昆明", "开封", "可克达拉市", "昆玉市", "克拉玛依", "克孜勒苏柯尔克孜自治州", "喀什地区", "拉萨", "兰州", "六盘水", "柳州", "洛阳", "辽源", "林芝", "泸州", "丽江", "连云港", "龙岩", "临沧", "辽阳", "廊坊", "临汾", "乐山", "吕梁", "漯河", "丽水", "乐东黎族自治县", "陇南", "临高", "临沂", "临夏回族自治州", "六安", "娄底", "来宾", "陵水黎族自治县", "聊城", "凉山彝族自治州", "马鞍山", "绵阳", "茂名", "牡丹江", "眉山", "梅州", "南京", "南昌", "南宁", "宁波", "那曲", "南通", "南平", "宁德", "内江", "南充", "南阳", "怒江傈僳族自治州" ],
    "PQRST" : [ "莆田", "萍乡", "攀枝花", "平顶山", "普洱", "平凉", "濮阳", "盘锦", "齐齐哈尔", "青岛", "曲靖", "秦皇岛", "泉州", "黔西南布依族苗族自治州", "钦州", "衢州", "黔东南苗族侗族自治州", "七台河", "黔南布依族苗族自治州", "庆阳", "潜江", "琼海", "琼中黎族苗族自治县", "清远", "日喀则", "日照", "上海", "沈阳", "石家庄", "石嘴山", "韶关", "四平", "十堰", "深圳", "三明", "双鸭山", "石河子", "山南", "苏州", "邵阳", "汕头", "朔州", "双河市", "绍兴", "三亚", "松原", "三沙", "遂宁", "商洛", "上饶", "绥化", "三门峡", "随州", "宿州", "宿迁", "汕尾", "商丘", "神农架", "台湾", "天津", "太原", "唐山", "铜川", "通化", "通辽", "天水", "铜仁", "铜陵", "泰安", "吐鲁番", "台州", "铁岭", "泰州", "天门", "屯昌", "塔城地区", "铁门关", "图木舒克" ],
    "WXYZ" : [ "武汉", "芜湖", "无锡", "乌海", "吴忠", "温州", "梧州", "渭南", "武威", "潍坊", "乌鲁木齐", "乌兰察布", "威海", "文山壮族苗族自治州", "万宁", "文昌", "五指山", "五家渠", "新星市", "香港", "西安", "西宁", "厦门", "徐州", "湘潭", "咸阳", "邢台", "襄阳", "新余", "新乡", "孝感", "忻州", "兴安盟", "许昌", "锡林郭勒盟", "咸宁", "西双版纳傣族自治州", "湘西土家族苗族自治州", "信阳", "宣城", "仙桃", "银川", "阳泉", "玉溪", "宜昌", "延安", "烟台", "鹰潭", "岳阳", "伊春", "玉树藏族自治州", "营口", "运城", "榆林", "延边朝鲜族自治州", "宜春", "益阳", "玉林", "盐城", "扬州", "永州", "宜宾", "阳江", "雅安", "伊犁哈萨克自治州", "云浮", "郑州", "株洲", "自贡", "淄博", "遵义", "枣庄", "珠海", "中卫", "昭通", "漳州", "张家口", "张掖", "张家界", "湛江", "舟山", "肇庆", "镇江", "周口", "驻马店", "资阳", "中山" ]
}

industries_bosszhipin =[
    '互联网', '电子商务', '计算机软件', '生活服务(O2O)', '企业服务', '医疗健康', '游戏', '社交网络与媒体', '人工智能', '云计算', '在线教育', '计算机服务', '大数据', '广告营销', '物联网', '新零售', '信息安全', 
    '半导体/芯片', '电子/硬件开发', '通信/网络设备', '智能硬件/消费电子', '运营商/增值服务', '计算机硬件', '电子/半导体/集成电路', 
    '餐饮', '美容', '美发', '酒店/民宿', '休闲/娱乐', '运动/健身', '保健/养生', '家政服务', '旅游/景区', '婚庆/摄影', '宠物服务', '回收/维修', '美容/美发', '其他生活服务', 
    '批发/零售', '进出口贸易', '食品/饮料/烟酒', '服装/纺织', '家具/家居', '家用电器', '日化', '珠宝/首饰', '家具/家电/家居', '其他消费品', 
    '装修装饰', '房屋建筑工程', '土木工程', '机电工程', '物业管理', '房地产中介/租赁', '建筑材料', '房地产开发经营', '建筑设计', '建筑工程咨询服务', '土地与公共设施管理', '工程施工', 
    '培训/辅导机构', '职业培训', '学前教育', '学校/学历教育', '学术/科研', 
    '文化艺术/娱乐', '体育', '广告/公关/会展', '广播/影视', '新闻/出版', 
    '通用设备', '专用设备', '电气机械/器材', '金属制品', '非金属矿物制品', '橡胶/塑料制品', '化学原料/化学制品', '仪器仪表', '自动化设备', '印刷/包装/造纸', '铁路/船舶/航空/航天制造', '计算机/通信/其他电子设备', '新材料', '机械设备/机电/重工', '仪器仪表/工业自动化', '原材料及加工/模具', '其他制造业', 
    '咨询', '财务/审计/税务', '人力资源服务', '法律', '检测/认证/知识产权', '翻译', '其他专业服务', 
    '医疗服务', '医美服务', '医疗器械', 'IVD', '生物/制药', '医药批发零售', '医疗研发外包', 
    '新能源汽车', '汽车智能网联', '汽车经销商', '汽车后市场', '汽车研发/制造', '汽车零部件', '摩托车/自行车制造', '4S店/后市场', 
    '即时配送', '快递', '公路物流', '同城货运', '跨境物流', '装卸搬运和仓储业', '客运服务', '港口/铁路/公路/机场', '交通/运输', '物流/仓储', 
    '光伏', '储能', '动力电池', '风电', '其他新能源', '环保', '化工', '电力/热力/燃气/水利', '石油/石化', '矿产/地质', '采掘/冶炼', '新能源', 
    '互联网金融', '银行', '投资/融资', '证券/期货', '基金', '保险', '租赁/拍卖/典当/担保', '信托', '财富管理', '其他金融业', 
    '农/林/牧/渔', '非盈利机构', '政府/公共事业', '其他行业'
]

system_prompt_bosszhipin = '''
你能根据用户发送的简历内容和额外补充的指示，按下面要求返回岗位过滤设置组合：
1.你的返回是一个标准合法的json字符串，具体内容示例如下：
{"岗位关键词":["产品经理","销售总监"],"城市":["武汉","深圳"],"工作区域":["武昌区","南山区"],"求职类型":"全职","薪资待遇":"10-20k","工作经验":["1-3年","3-5年"],"学历要求":["本科","硕士"],"公司行业":["电子商务","进出口贸易","在线教育"],"公司规模":["20-99人","100-499人"]}
2.各字段的取值要求如下：
 "岗位关键词":list[str]，可自定义，list里至少要有一个岗位关键词
 "城市":list[str]，简历或指示里提到的全部求职目标城市(str里不要加"市"字，比如"武汉"合法，但是"武汉市"非法)，list里至少要有一个城市
 "工作区域":list[str]，简历或指示里提到的全部求职目标区域/县级市/县(str举例:1."武昌区" 2."高碑店市" 3."岳西县")，如果用户没有明确要求，则返回空list
 "求职类型":str，合法取值只有："不限"，"全职"，"兼职"，如果用户没有明确要求，则返回"不限"
 "薪资待遇":str，合法的值只有："不限"，"3K以下"，"3-5K"，"5-10K"，"10-20K"，"20-50K"，"50K以上"，（如果简历或指示里没有明确要求，你需要返回"不限"！）
 "工作经验":list[str]，str的合法取值有："不限"，"在校生"，"应届生"，"经验不限"，"1年以内"，"1-3年"，"3-5年"，"5-10年"，"10年以上"，（如果简历或指示里没有明确要求，你需要返回空list！）
 "学历要求":list[str]，str的合法取值有："不限"，"初中及以下"，"中专/中技"，"高中"，"大专"，"本科"，"硕士"，"博士"，（如果简历或指示里没有明确要求，你需要返回空list！）
 "公司规模":list[str]，str的合法取值有："不限"，"0-20人"，"20-99人"，"100-499人"，"500-999人"，"1000-9999人"，"10000人以上"（如果简历或指示里没有明确要求，你需要返回空list！）
''' + (f' "公司行业":list[str]，str的合法取值有：{', '.join([f'"{item}"' for item in industries_bosszhipin])} ，list最多包含3个元素')


def login_bosszhipin():
    # Chrome WebDriver
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install())) 
    # 配置反爬浏览器
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")  # 隐藏自动化标志
    options.add_argument("--start-maximized")  # 最大化窗口
    options.add_argument("--disable-notifications")  # 禁用通知
    # 设置随机User-Agent
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")
    # 初始化浏览器
    print("正在初始化浏览器")
    driver = uc.Chrome(
        options=options, 
        # version_main=138,  
        # use_subprocess=False
    )
    print("浏览器初始化完毕")
    try:
        print("浏览器即将打开，请在浏览器打开完毕后手动登录BOSS直聘")
        # Navigate to Boss Zhipin website
        driver.get("https://www.zhipin.com/web/user/?ka=header-login")   
        # Prompt user to log in manually
        print("请在我打开的浏览器中手动登录BOSS直聘，登陆完成后放着等我来操作就好")  
        # Get the initial URL
        initial_url = driver.current_url  
        # Poll for page redirection to detect successful login
        timeout = 300  # Maximum wait time in seconds
        poll_interval = 2  # Check every 2 seconds
        elapsed_time = 0
        login_flag = False
        while elapsed_time < timeout:
            current_url = driver.current_url
            if current_url != initial_url:
                print("恭喜您，登录成功，你可以最小化我的浏览器，让我自己来操作它就好了~")
                login_flag = True
                break
            time.sleep(poll_interval)
            elapsed_time += poll_interval
        if login_flag:
            return {"result":"succeed", "driver": driver}
        else:
            print("在5分钟内，您没能登录您的BOSS直聘账号，于是我先关闭了浏览器")
            return {"result":"failed", "failure": "Login not completed within timeout period."}        
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"result":"failed", "failure": str(e)}

#检验过滤条件的合法性，判断json字符串的合法性，返回字段的合法性
def is_legal(response:str):
    try:
        requirements = json.loads(response)
        return True
    except:
        return False
        
#自动识别txt, pdf, word文档，并返回文本内容
def read_cv(local_cv_path: str) -> str:
    ext = os.path.splitext(local_cv_path)[1].lower()
    if ext == ".txt":
        with open(local_cv_path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".pdf":
        text = ""
        with fitz.open(local_cv_path) as doc:
            for page in doc:
                text += page.get_text("text")
        return text
    elif ext == ".docx":
        doc = docx.Document(local_cv_path)
        # 只提取非空段落并合并
        paras = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paras)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

# 生成多种岗位过滤条件组合
def job_requirements_bosszhipin(local_cv_path: str, user_instruction:str):
    try:
        #打开CV,读取内容
        cv_content = read_cv(local_cv_path) 
    except Exception as e:
        return {"result":"failed", "failure": str(e)}
    #将CV内容送往大模型，要求返回所有合适的岗位过滤设置组合:
    system_prompt = "你能根据用户发送的简历内容和额外补充的指示，按下面要求返回岗位过滤设置组合：\n1.你的返回是一个标准合法的json字符串（能够被json.loads直接解析），具体内容示例如下：\n{\"岗位关键词\":[\"产品经理\",\"销售总监\"],\"城市\":[\"武汉\",\"深圳\"],\"工作区域\":[\"武昌区\",\"南山区\"],\"求职类型\":\"全职\",\"薪资待遇\":\"10-20k\",\"工作经验\":[\"1-3年\",\"3-5年\"],\"学历要求\":[\"本科\",\"硕士\"],\"公司行业\":[\"电子商务\",\"进出口贸易\",\"在线教育\"],\"公司规模\":[\"20-99人\",\"100-499人\"]}\n2.各字段的取值要求如下：\n \"岗位关键词\":list[str]，可自定义，list里至少要有一个岗位关键词\n \"城市\":list[str]，简历或指示里提到的全部求职目标城市(str里不要加\"市\"字，比如\"武汉\"合法，但是\"武汉市\"非法)，list里至少要有一个城市\n \"工作区域\":list[str]，简历或指示里提到的全部求职目标区域/县级市/县(str举例:1.\"武昌区\" 2.\"高碑店市\" 3.\"岳西县\")，如果用户没有明确要求，则返回空list\n \"求职类型\":str，合法取值只有：\"不限\"，\"全职\"，\"兼职\"，如果用户没有明确要求，则返回\"不限\"\n \"薪资待遇\":str，合法的值只有：\"不限\"，\"3K以下\"，\"3-5K\"，\"5-10K\"，\"10-20K\"，\"20-50K\"，\"50K以上\"，（如果简历或指示里没有明确要求，你需要返回\"不限\"！）\n \"工作经验\":list[str]，str的合法取值有：\"不限\"，\"在校生\"，\"应届生\"，\"经验不限\"，\"1年以内\"，\"1-3年\"，\"3-5年\"，\"5-10年\"，\"10年以上\"，（如果简历或指示里没有明确要求，你需要返回空list！）\n \"学历要求\":list[str]，str的合法取值有：\"不限\"，\"初中及以下\"，\"中专/中技\"，\"高中\"，\"大专\"，\"本科\"，\"硕士\"，\"博士\"，（如果简历或指示里没有明确要求，你需要返回空list！）\n \"公司规模\":list[str]，str的合法取值有：\"不限\"，\"0-20人\"，\"20-99人\"，\"100-499人\"，\"500-999人\"，\"1000-9999人\"，\"10000人以上\"（如果简历或指示里没有明确要求，你需要返回空list！）\n \"公司行业\":list[str]，str的合法取值有：\"互联网\", \"电子商务\", \"计算机软件\", \"生活服务(O2O)\", \"企业服务\", \"医疗健康\", \"游戏\", \"社交网络与媒体\", \"人工智能\", \"云计算\", \"在线教育\", \"计算机服务\", \"大数据\", \"广告营销\", \"物联网\", \"新零售\", \"信息安全\", \"半导体/芯片\", \"电子/硬件开发\", \"通信/网络设备\", \"智能硬件/消费电子\", \"运营商/增值服务\", \"计算机硬件\", \"电子/半导体/集成电路\", \"餐饮\", \"美容\", \"美发\", \"酒店/民宿\", \"休闲/娱乐\", \"运动/健身\", \"保健/养生\", \"家政服务\", \"旅游/景区\", \"婚庆/摄影\", \"宠物服务\", \"回收/维修\", \"美容/美发\", \"其他生活服务\", \"批发/零售\", \"进出口贸易\", \"食品/饮料/烟酒\", \"服装/纺织\", \"家具/家居\", \"家用电器\", \"日化\", \"珠宝/首饰\", \"家具/家电/家居\", \"其他消费品\", \"装修装饰\", \"房屋建筑工程\", \"土木工程\", \"机电工程\", \"物业管理\", \"房地产中介/租赁\", \"建筑材料\", \"房地产开发经营\", \"建筑设计\", \"建筑工程咨询服务\", \"土地与公共设施管理\", \"工程施工\", \"培训/辅导机构\", \"职业培训\", \"学前教育\", \"学校/学历教育\", \"学术/科研\", \"文化艺术/娱乐\", \"体育\", \"广告/公关/会展\", \"广播/影视\", \"新闻/出版\", \"通用设备\", \"专用设备\", \"电气机械/器材\", \"金属制品\", \"非金属矿物制品\", \"橡胶/塑料制品\", \"化学原料/化学制品\", \"仪器仪表\", \"自动化设备\", \"印刷/包装/造纸\", \"铁路/船舶/航空/航天制造\", \"计算机/通信/其他电子设备\", \"新材料\", \"机械设备/机电/重工\", \"仪器仪表/工业自动化\", \"原材料及加工/模具\", \"其他制造业\", \"咨询\", \"财务/审计/税务\", \"人力资源服务\", \"法律\", \"检测/认证/知识产权\", \"翻译\", \"其他专业服务\", \"医疗服务\", \"医美服务\", \"医疗器械\", \"IVD\", \"生物/制药\", \"医药批发零售\", \"医疗研发外包\", \"新能源汽车\", \"汽车智能网联\", \"汽车经销商\", \"汽车后市场\", \"汽车研发/制造\", \"汽车零部件\", \"摩托车/自行车制造\", \"4S店/后市场\", \"即时配送\", \"快递\", \"公路物流\", \"同城货运\", \"跨境物流\", \"装卸搬运和仓储业\", \"客运服务\", \"港口/铁路/公路/机场\", \"交通/运输\", \"物流/仓储\", \"光伏\", \"储能\", \"动力电池\", \"风电\", \"其他新能源\", \"环保\", \"化工\", \"电力/热力/燃气/水利\", \"石油/石化\", \"矿产/地质\", \"采掘/冶炼\", \"新能源\", \"互联网金融\", \"银行\", \"投资/融资\", \"证券/期货\", \"基金\", \"保险\", \"租赁/拍卖/典当/担保\", \"信托\", \"财富管理\", \"其他金融业\", \"农/林/牧/渔\", \"非盈利机构\", \"政府/公共事业\", \"其他行业\" ，list最多包含3个元素"
    user_prompt = "简历内容如下：\n" + cv_content + "补充要求：\n" + user_instruction
    content = request_LLM_api(filter_generate_model_config, user_prompt, system_prompt)
    requirements = json.loads(content)
    return {"result":"succeed","requirements":requirements}


#没有完成
def upload_cv_on_bosszhipin(driver, local_cv_path: str):
    try:
        if not os.path.exists(local_cv_path):
            raise FileNotFoundError(f"CV file not found at: {local_cv_path}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # profile_link = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '个人中心') or contains(text(), '我的') or contains(@href, 'user')]"))
        # )
        # profile_link.click()
        resume_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '附件上传') or contains(@href, 'resume')]"))
        )
        resume_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '上传附件简历') or contains(text(), '添加简历')]"))
        )
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(os.path.abspath(local_cv_path))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '上传成功') or contains(text(), '简历已上传')]"))
        )
        print("CV uploaded successfully to Boss Zhipin resume library.")
        return {"result":"succeed","driver":driver}
    except Exception as e:
        print(f"An error occurred during CV upload: {e}")
        return {"result":"failed","failure":str(e)}

# def scroll_to_bottom_like_user(driver, step=500, pause=3):
#     print("开始模拟真实滚动到页面底部...")
#     last_height = driver.execute_script("return document.body.scrollHeight")
#     actions = ActionChains(driver)
#     current_position = 0
#     while current_position < last_height:
#         # 模拟鼠标移动（扰动）
#         actions.move_by_offset(0, 1).perform()
#         time.sleep(0.1)
#         # 滚动一步
#         driver.execute_script(f"window.scrollBy(0, {step});")
#         current_position += step
#         print(f"已滚动至：{current_position}")
#         time.sleep(pause)
#         # 检查是否出现更多内容（懒加载）
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height > last_height:
#             last_height = new_height
#     print("已滚动至页面底部。")

def scroll_to_bottom_like_user(driver, step=10000, pause=3):
    print("开始模拟真实滚动到页面底部...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    actions = ActionChains(driver)
    while True:
        # 模拟鼠标移动（扰动）
        actions.move_by_offset(0, 1).perform()
        time.sleep(0.1)
        # 滚动足够大的一步（step一定大于静态页面高度）
        driver.execute_script(f"window.scrollBy(0, {step});")
        print(f"已拉到页面底部")
        time.sleep(pause)
        # 检查是否出现更多内容（懒加载）
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height > last_height:
            last_height = new_height
        else:
            break
    print("已完成全部内容加载")


def filter_jobs_like_user_bosszhipin(driver, requirement):
    #网页元素筛选条件
    filters = {
        "岗位关键词": {
            "locator": (By.CSS_SELECTOR, "input[placeholder='搜索职位、公司']"),
            "type": "input",
            "action": lambda el, val: [el.clear(), el.send_keys(val), el.send_keys(Keys.ENTER)]
        },
        "城市": {
            "locator": (By.XPATH, "//div[@ka='switch_city_dialog_open']"),
            "type": "city",
            "option_letter": lambda val: (By.XPATH, f"//ul[@class='city-char-list']/li[text()='{val}']"),
            "option_city": lambda val: (By.XPATH, f"//div[@class='list-select-list']/a[normalize-space(.)='{val}']")
        },
        "工作区域": {
            "locator": (By.XPATH, "//div[contains(@class, 'filter-city-area') and contains(@class, 'city-area-select') and @placeholder='工作区域']"),
            "type": "multi",
            "option": lambda val: (By.XPATH, f"//li[starts-with(@ka,'sel-business-') and normalize-space(text()[1])='{val}']")
        },
        "求职类型": {
            "locator": (By.XPATH, "//div[@class='current-select' and .//span[text()='求职类型']]//following-sibling::div[@class='filter-select-dropdown']"),
            "type": "single",
            "option": lambda val: (By.XPATH, f"//li[starts-with(@ka,'sel-job-rec-jobType-') and normalize-space(text()[1])='{val}']")
        },
        "薪资待遇": {
            "locator": (By.XPATH, "//div[@class='condition-filter-select' and .//span[text()='薪资待遇']]//following-sibling::div[@class='filter-select-dropdown']"),
            "type": "single",
            "option": lambda val: (By.XPATH, f"//li[starts-with(@ka,'sel-job-rec-salary-') and normalize-space(text()[1])='{val}']")
        },
        "工作经验": {
            "locator": (By.XPATH, "//div[contains(@class, 'current-select') and .//span[text()='工作经验']]//following-sibling::div[@class='filter-select-dropdown']"),
            "type": "multi",
            "option": lambda val: (By.XPATH, f"//li[starts-with(@ka,'sel-job-rec-exp-') and normalize-space(text()[1])='{val}']")
        },
        "学历要求": {
            "locator": (By.XPATH, "//div[contains(@class, 'current-select') and .//span[text()='学历要求']]//following-sibling::div[@class='filter-select-dropdown']"),
            "type": "multi",
            "option": lambda val: (By.XPATH, f"//li[starts-with(@ka,'sel-job-rec-degree-') and normalize-space(text()[1])='{val}']")
        },
        "公司行业": {
            "locator": (By.XPATH, "//div[contains(@class, 'condition-industry-select') and .//span[text()='公司行业']]//following-sibling::div[@class='filter-select-dropdown']"),
            "type": "multi",
            "option": lambda val: (By.XPATH, f"//div[@class='select-list']/a[contains(text(), '{val}')]")
        },           
        "公司规模": {
            "locator": (By.XPATH, "//div[contains(@class, 'current-select') and .//span[text()='公司规模']]//following-sibling::div[@class='filter-select-dropdown']"),
            "type": "multi",
            "option": lambda val: (By.XPATH, f"//li[starts-with(@ka,'sel-job-rec-scale-') and normalize-space(text()[1])='{val}']")
        },
    }
    print(f"开始投递设置组合：{requirement}")
    for key, value in requirement.items():
        if key not in filters:
            print(f"筛选条件 '{key}' 不存在，跳过")
            continue
        filter_config = filters[key]
        print(f"开始处理筛选条件: {key} = {value}")
        try:
            #输入框填写和确认
            if filter_config["type"] == "input":
                print("随机等待几秒，确保操作安全......")
                time.sleep(random.uniform(2, 5))
                element = WebDriverWait(driver, timeout=30).until(EC.element_to_be_clickable(filter_config["locator"]))
                print(f"我成功找到: {key}")
                print(f"正在执行输入操作: {value}")
                action = filter_config["action"]
                action(element, value)
                print(f"已搜索关键词: {value}")
            #城市设置
            elif filter_config["type"] == "city":
                print("随机等待几秒，确保操作安全......")
                time.sleep(random.uniform(2, 5))
                element = WebDriverWait(driver, timeout=30).until(EC.element_to_be_clickable(filter_config["locator"]))
                print(f"我成功找到: {key}")
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                driver.execute_script("arguments[0].click();", element)
                print(f"已强制点击: {key}")
                #匹配首字母选项卡，点击
                print("随机等待几秒，确保操作安全......")
                time.sleep(random.uniform(2, 5))
                for start_letters, cities in city_math_bosszhipin.items():
                    if value in cities:
                        print(f"匹配到 {value} 在 {start_letters} 选项卡内")
                        break
                element = WebDriverWait(driver, timeout=30).until(EC.element_to_be_clickable(filter_config["option_letter"](start_letters)))
                print(f"我成功找到: {start_letters} 按钮")
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                driver.execute_script("arguments[0].click();", element)
                print(f"已强制点击: {start_letters} 按钮")
                #匹配城市按钮，点击
                print("随机等待几秒，确保操作安全......")
                time.sleep(random.uniform(2, 5))
                element = WebDriverWait(driver, timeout=30).until(EC.element_to_be_clickable(filter_config["option_city"](value)))
                print(f"我成功找到: {value} 按钮")
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                driver.execute_script("arguments[0].click();", element)
                print(f"已强制点击: {value} 按钮")                    
            #多选选项卡
            elif filter_config["type"] == "multi":
                for val in value:    
                    try:
                        print("进入3秒等待，确保操作安全......")
                        time.sleep(random.uniform(2, 5))
                        print(f"正在定位 '{key}' 元素")
                        work_area_element = WebDriverWait(driver, 30).until( EC.presence_of_element_located(filter_config["locator"]) )
                        print(f"成功定位到 '{key}' 元素")
                    except Exception as e:
                        print(f"没能找到：{key}")    
                    # 定位工作区域元素后
                    print("进入3秒等待，确保操作安全......")
                    time.sleep(random.uniform(2, 5))
                    driver.execute_script("arguments[0].style.display = 'block';", work_area_element)
                    print("我已设置下拉菜单为可见")
                    if key == "公司行业":
                        options = driver.find_elements(By.XPATH, f"{filter_config['locator'][1]}//a")
                    else:
                        options = driver.find_elements(By.XPATH, f"{filter_config['locator'][1]}//li")
                    option_texts = []
                    for opt in options:
                        # 方法1: 使用textContent属性（推荐）
                        text = driver.execute_script("return arguments[0].textContent;", opt)
                        # 去除图标文本，只保留选项文本
                        text = text.replace('', '').strip()  # 去除可能的图标字符
                        option_texts.append(text)
                    print("可用选项：", option_texts)
                    if val in option_texts:
                        print("进入3秒等待，确保操作安全......")
                        time.sleep(random.uniform(2, 5))                    
                        print(f"正在锁定：{val}")
                        option = WebDriverWait( driver, timeout=10).until(EC.presence_of_element_located(filter_config["option"](val)))
                        print(f"成功锁定：{val}")
                    else:
                        print(f"选项中没有{val}")
                        continue
                    if not option.is_selected():
                        try:
                            # 尝试 JavaScript 强制点击
                            driver.execute_script("arguments[0].scrollIntoView(true);", option)
                            driver.execute_script("arguments[0].click();", option)
                            print(f"我已选中选项: {val}")
                        except Exception as e:
                            # 回退到 ActionChains 点击
                            print(f"JavaScript 点击失败，尝试 ActionChains: {str(e)}")
                            ActionChains(driver).move_to_element(option).click().perform()
                            print(f"已通过 ActionChains 选中选项: {val}")
            #单选项筛选
            elif filter_config["type"] == "single":
                try:
                    print("进入3秒等待，确保操作安全......")
                    time.sleep(random.uniform(2, 5))
                    print(f"正在定位 '{key}' 元素")
                    work_area_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(filter_config["locator"])
                    )
                    print(f"成功定位到 '{key}' 元素")
                except Exception as e:
                    print(f"没能找到：{key}")

                # 定位工作区域元素后
                print("进入3秒等待，确保操作安全......")
                time.sleep(random.uniform(2, 5))
                driver.execute_script("arguments[0].style.display = 'block';", work_area_element)
                print("我已设置下拉菜单为可见")

                print("进入3秒等待，确保操作安全......")
                time.sleep(random.uniform(2, 5))
                options = driver.find_elements(By.XPATH, f"{filter_config['locator'][1]}//li")
                option_texts = []
                for opt in options:
                    # 方法1: 使用textContent属性（推荐）
                    text = driver.execute_script("return arguments[0].textContent;", opt)
                    # 去除图标文本，只保留选项文本
                    text = text.replace('', '').strip()  # 去除可能的图标字符
                    option_texts.append(text)
                print("可用选项：", option_texts)

                if value in option_texts:
                    print("进入3秒等待，确保操作安全......")
                    time.sleep(random.uniform(2, 5))                      
                    print(f"正在锁定：{value}")
                    option = WebDriverWait( driver, timeout=10).until(EC.presence_of_element_located(filter_config["option"](value)))
                    print(f"成功锁定：{value}")
                else:
                    print(f"选项中没有{value}")
                    continue

                if not option.is_selected():
                    try:
                        # 尝试 JavaScript 强制点击
                        driver.execute_script("arguments[0].scrollIntoView(true);", option)
                        driver.execute_script("arguments[0].click();", option)
                        print(f"我已选中选项: {value}")
                    except Exception as e:
                        # 回退到 ActionChains 点击
                        print(f"JavaScript 点击失败，尝试 ActionChains: {str(e)}")
                        ActionChains(driver).move_to_element(option).click().perform()
                        print(f"已通过 ActionChains 选中选项: {value}")
            else:
                print(f"未知的筛选类型: {filter_config['type']}")
        except TimeoutException as te:
            print(f"超时错误在处理 {key}: {str(te)}")
            return False
        except NoSuchElementException as nse:
            print(f"未找到元素在处理 {key}: {str(nse)}")
            return False
        except WebDriverException as wde:
            print(f"WebDriver错误在处理 {key}: {str(wde)}")
            return False


#直接URL传参过滤职位
def filter_jobs_by_url(driver, requirement):
    url = "https://www.zhipin.com/web/geek/jobs?"
    #城市
    try:
        city = requirement["城市"]
        url = url + "city=" + city_code_bosszhipin[city]
    except:
        pass
    #求职类型
    try:
        job_type = requirement["求职类型"]
        if job_type != "不限":
            url = url + "&jobType=" + job_type_code_bosszhipin[job_type]
    except:
        pass
    #薪资待遇
    try:
        salary = requirement["薪资待遇"]
        if salary != "不限":
            url = url + "&salary=" + salary_code_bosszhipin[salary]
    except:
        pass
    #工作经验
    try:
        experience = requirement["工作经验"]
        if experience:
            url = url + "&experience="
            url = url + ",".join([experience_code_bosszhipin[exp] for exp in experience])
    except:
        pass
    #学历要求
    try:
        degree = requirement["学历要求"]
        if degree:
            url = url + "&degree="
            url = url + ",".join([degree_code_bosszhipin[deg] for deg in degree])
    except:
        pass            
    #行业
    try:
        industries = requirement["公司行业"]
        if industries:
            url = url + "&industry="
            url = url + ",".join([industry_code_bosszhipin[industry] for industry in industries])
    except:
        pass     
    #公司规模
    try:
        scale = requirement["公司规模"]
        if scale:
            url = url + "&scale="
            url = url + ",".join([scale_code_bosszhipin[sca] for sca in scale])
    except:
        pass 
    #岗位关键词
    try:
        url = url + "&query=" + requirement["岗位关键词"]
    except:
        pass 
    #跳转到新url
    # print(url)
    driver.get(url)
    print("已初步完成过滤设置，接下来我将操纵浏览器选定工作区域......")
    time.sleep(3)
    return True

#过滤职位，并给BOSS打招呼
async def send_greetings_on_bosszhipin(driver, requirement: dict, num_chat_per_requirement:int=200):
    try:
        #初始化对话计数器
        chat_count = 0
        #过滤职位
        filter_jobs_by_url(driver, requirement)
        work_area_requirement ={"工作区域": requirement["工作区域"]}
        filter_jobs_like_user_bosszhipin(driver, work_area_requirement)
        #将页面拉倒最下，加载所有信息
        time.sleep(3)
        scroll_to_bottom_like_user(driver)
        #匹配所有职位信息
        time.sleep(3)
        job_names = driver.find_elements(By.XPATH, "//div[@class='job-title clearfix']/a[@class='job-name']")
        boss_names = driver.find_elements(By.XPATH, '//span[@class="boss-name"]')
        company_locations = driver.find_elements(By.XPATH, '//span[@class="company-location"]')
        job_requirements = driver.find_elements(By.XPATH, "//ul[@class='tag-list' and @data-v-7a4b5b6e='']")
        print(f"目前一共找到{len(job_names)}个职位")
        #从文件记录读取已经投递过的职位
        try:
            with open(globals.PROJECT_FILE_PATH, "r", encoding="utf-8") as f:
                chat_records = json.load(f)
                if not isinstance(chat_records, list):
                    chat_records = []
            print("我成功读取了之前的投递记录")
        except FileNotFoundError:
            print("我没有找到之前的投递记录")
            chat_records = []
        records_set = {
            (record.get("岗位名称"), record.get("公司名称"), record.get("公司地址"), record.get("岗位要求"))
            for record in chat_records
        }
        #过滤掉已经投递过的职位
        filtered_jobs = []
        for(jn,bn,cl, jr) in zip(job_names, boss_names, company_locations, job_requirements):
            job_name = jn.text.strip()
            boss_name = bn.text.strip()
            company_location = cl.text.strip()
            job_requirement = jr.text.strip()
            if (job_name, boss_name, company_location, job_requirement) not in records_set:
                filtered_jobs.append((jn, bn, cl, jr))
        if filtered_jobs:
            job_names, boss_names, company_locations, job_requirements = zip(*filtered_jobs)
        else:
            job_names, boss_names, company_locations, job_requirements = [], [], [], []
        print(f"过滤以前投递过的职位，本次目标职位有{len(job_names)}个，即将开始投递......")
        #逐个职位打招呼
        for attempt_count, job in enumerate(job_names):
            #已经沟通了计划数量的BOSS，跳出循环
            if chat_count>=num_chat_per_requirement:
                break
            print("先随机等待几秒钟，保证安全操作......")
            time.sleep(random.uniform(2, 5))
            try:
                #强制点击job-name元素
                driver.execute_script("arguments[0].click();", job)
            except:
                #从个人中心回来，页面刷新了
                continue
            print("我已经点击了职位卡片")
            print("先随机等待几秒钟，保证安全操作......")
            time.sleep(random.uniform(2, 5))
            #然后点击“立即沟通”按钮
            chat_button = (driver.find_elements(By.XPATH, "//a[@class='op-btn op-btn-chat' and text()='立即沟通']"))[0]
            driver.execute_script("arguments[0].click();", chat_button)
            print("我已经点击了“立即沟通”")
            #然后强制点击“留在此页”按钮
            print("先随机等待几秒钟，保证安全操作......")
            time.sleep(random.uniform(2, 5))
            try:
                #沟通成功   
                stay_button = WebDriverWait(driver, timeout=5).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(concat(' ', normalize-space(@class), ' '), ' cancel-btn ') and normalize-space(.)='留在此页']")))
                print("恭喜我们，成功给BOSS打了一个招呼！")
                driver.execute_script("arguments[0].click();", stay_button)
                print("我已点击“留在此页”按钮")
                #写入投递记录
                try:
                    new_record = {
                        "岗位名称": job_names[attempt_count].text.strip(),
                        "公司名称": boss_names[attempt_count].text.strip(),
                        "公司地址": company_locations[attempt_count].text.strip(),
                        "岗位要求": job_requirements[attempt_count].text.strip()
                    }
                except:
                    new_record={ 
                        "岗位名称": "读取失败", 
                        "公司名称": "读取失败", 
                        "公司地址": "读取失败", 
                        "岗位要求": "岗位要求" 
                    }
                try:
                    os.makedirs(globals.PROJECT_PATH,exist_ok=True)
                    with open(globals.PROJECT_FILE_PATH, "r", encoding="utf-8") as f:
                        chat_records = json.load(f)
                        if not isinstance(chat_records, list):
                            chat_records = []
                    # print("成功读取了之前的投递记录")
                except FileNotFoundError:
                    chat_records = []
                try:
                    chat_records.append(new_record)
                    with open(globals.PROJECT_FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(chat_records, f, ensure_ascii=False, indent=2)
                    print("已将刚才投递的岗位写入投递记录，方便下次跳过")
                    #将文件路径返回给前端
                    print(os.path.abspath(globals.PROJECT_FILE_PATH))
                    qprint(f"<file>{os.path.abspath(globals.PROJECT_FILE_PATH)}")
                except:
                    pass
                #计数器更新
                chat_count+=1 
            except:
                #提示简历与岗位不符合
                print("提示你的简历与岗位不符合，我即将关闭提示弹窗，开始投下一个......")
                original_handle = driver.current_window_handle
                print("正在寻找“个人中心”按钮......")
                personla_center_button = WebDriverWait(driver, timeout=10).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='default-btn sure-btn' and text()='个人中心']")))
                personla_center_button.click()
                print("成功点击“个人中心”按钮")
                print("先随机等待几秒钟，保证安全操作......")
                time.sleep(random.uniform(2, 5))               
                WebDriverWait(driver, timeout=10).until(lambda d: len(d.window_handles) > 1)
                all_handles = driver.window_handles
                for handle in all_handles:
                    if handle != original_handle:
                        driver.switch_to.window(handle)
                        driver.close()               
                driver.switch_to.window(original_handle)
                print("关闭掉了新的标签页，重新回到简历投递页面")
                time.sleep(2)

        print(f"这一组关键词+过滤设置已投递完毕，共完成{chat_count}次投递，即将开启下一组设置......")
        #清空过滤设置（跳转https://www.zhipin.com/web/geek/jobs）
        driver.get("https://www.zhipin.com/web/geek/jobs")
        print("我已清空职位筛选设置，准备操作下一组设置......")
        print("先随机等待几秒钟，保证安全操作......")
        time.sleep(random.uniform(2, 5))
        return {"chat_count": chat_count}   
    except Exception as e:
        print(f"操作时遇到以外，终止了本组设置的投递: {str(e)}")
        return {"chat_count": chat_count}

#上Boss直聘给匹配的BOSS们打招呼
async def apply_on_bosszhipin(cv_path:str, user_instruction:str=""):
    #根据简历和用户指示，生成搜索+过滤设置组合
    get_requirements_result = job_requirements_bosszhipin(cv_path, user_instruction)
    if get_requirements_result["result"] == "failed":
        return {"result":"failed","failure":"failed to extract requirements for jobs"}
    requirements = get_requirements_result["requirements"]
    requirement_list = []
    for city in requirements["城市"]:
        for keyword in requirements["岗位关键词"]:
            requirement = copy.deepcopy(requirements)
            requirement["城市"] = city
            requirement["岗位关键词"] = keyword
            requirement_list.append(requirement)  
    #根据BOSS每日打招呼上限来分流（每天上限200次）
    num_chat_per_requirement = int(200/len(requirement_list))
    print(f"一共为您规划了{len(requirement_list)}组关键词+职位过滤设置组合，具体内容如下：")
    print(*requirement_list, sep='\n')
    print(f"BOSS直聘每日主动沟通总上限为200次，所以我将会为以上每种组合平均投递{num_chat_per_requirement}次")
    #开始操作
    chat_count = 0
    print("我即将打开浏览器进行操作......")
    login_result = login_bosszhipin()
    driver = login_result["driver"]
    for requirement in requirement_list:
        apply_result =await send_greetings_on_bosszhipin(driver, requirement, num_chat_per_requirement)
        chat_count_requirement = apply_result["chat_count"]
        chat_count+=chat_count_requirement
    return {"successful_chat_count": chat_count}




###########################################     工具注册    #############################################################
tool_registry = {
    "apply_on_bosszhipin": apply_on_bosszhipin,
}
tools = [
    {
        "type": "function",
        "function": {
            "name": "apply_on_bosszhipin",
            "description": "根据用户提供的简历和用户对所需岗位的补充指示，在BOSS直聘上筛选合适的岗位并投递简历（给BOSS打招呼）\n",
            "parameters": {
                "type": "object",
                "properties": {
                    "cv_path": {
                        "type": "string",
                        "description": "简历文件的合法本地路径（支持txt, word, pdf）"
                    },
                    "user_instruction": {
                        "type": "string",
                        "description": "用户对所需岗位的补充指示，自然语言描述（直接转述用户的原话即可）"
                    }
                },
                "required": ["cv_path"]
            }
        }
    },  
]


#############################################################################################################################

if __name__ == "__main__":
#BOSSZHIPIN测试
    # result = login_bosszhipin()
    # driver = result
    # requirement = {"岗位关键词":"产品经理","城市":"武汉","工作区域":["武昌区","南山区"],"求职类型":"全职","薪资待遇":["10-20K"],"工作经验":["1-3年"],"学历要求":["本科"],"公司行业":["电子商务","进出口贸易","在线教育"],"公司规模":["20-99人"]}
    # fd =send_greetings_on_bosszhipin(driver, requirement)
    # filter_jobs_by_url(requirement)
    result = apply_on_bosszhipin("./debug.txt","薪资没有要求")
    time.sleep(300)
    print(result)
 