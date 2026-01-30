#!/usr/bin/env python3
"""
和风天气综合查询脚本

使用方法:
    python get_weather.py <type> <location> [options]

参数:
    type      查询类型: now(实时), forecast(15天预报), warning(灾害预警), air(空气质量), indices(生活指数)
    location  城市ID（如 101010100）或经纬度（如 116.41,39.92）
    options   可选参数（仅 indices 需要）: --type 1,2,3

环境变量:
    QWEATHER_API_KEY: 和风天气 API Key（必需）

示例:
    python get_weather.py now 101010100
    python get_weather.py forecast 116.41,39.92
    python get_weather.py warning 101010100
    python get_weather.py air 116.41,39.92
    python get_weather.py indices 101010100 --type 1,2,3
"""

import os
import sys
import json
import requests
from typing import Dict, Any

# API 配置
#下方host要替换成自己的
API_HOST = "n43h2qkhvb.re.qweatherapi.com"
API_BASE_URL = f"https://{API_HOST}/v7"
AIR_API_BASE_URL = f"https://{API_HOST}/airquality/v1"
LANGUAGE = "zh"  # zh: 中文, en: 英文
UNIT = "m"       # m: 公制, i: 英制

# 生活指数类型映射
INDICES_TYPES = {
    "1": "运动指数", "2": "洗车指数", "3": "穿衣指数", "4": "钓鱼指数",
    "5": "紫外线指数", "6": "旅游指数", "7": "花粉过敏指数", "8": "舒适度指数",
    "9": "感冒指数", "10": "空气污染扩散条件指数", "11": "空调开启指数",
    "12": "太阳镜指数", "13": "化妆指数", "14": "晾晒指数", "15": "交通指数", "16": "防晒指数"
}


def get_api_key() -> str:
    """从环境变量获取 API Key"""
    api_key = os.environ.get("QWEATHER_API_KEY")
    if not api_key:
        print("错误: 未设置 QWEATHER_API_KEY 环境变量", file=sys.stderr)
        print("请运行: export QWEATHER_API_KEY='your_api_key'", file=sys.stderr)
        sys.exit(1)
    return api_key


def make_request(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """通用 API 请求函数"""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("错误: 网络连接失败，请检查网络连接", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("错误: 请求超时，请稍后重试", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"错误: HTTP 请求失败 ({e.response.status_code})", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


def check_response_code(data: Dict[str, Any]) -> bool:
    """检查响应状态码"""
    if data.get("code") != "200":
        error_msg = {
            "400": "请求错误，请检查参数格式",
            "401": "认证失败，请检查 API Key 是否正确",
            "402": "超过访问次数或余额不足",
            "403": "无访问权限",
            "404": "查询的数据不存在",
            "429": "超过限定的请求次数",
            "500": "服务器错误，请稍后重试"
        }
        code = data.get("code", "unknown")
        message = error_msg.get(code, f"未知错误 (代码: {code})")
        print(json.dumps({"error": message, "code": code}, ensure_ascii=False, indent=2), file=sys.stderr)
        return False
    return True


def fetch_now(location: str, api_key: str) -> Dict[str, Any]:
    """获取实时天气"""
    url = f"{API_BASE_URL}/weather/now"
    params = {"location": location, "key": api_key, "lang": LANGUAGE, "unit": UNIT}
    data = make_request(url, params)
    
    if not check_response_code(data):
        sys.exit(1)
    
    now = data.get("now", {})
    temp_unit = "°C" if UNIT == "m" else "°F"
    speed_unit = "km/h" if UNIT == "m" else "mph"
    
    return {
        "type": "实时天气",
        "updateTime": data.get("updateTime", ""),
        "temperature": f"{now.get('temp', 'N/A')}{temp_unit}",
        "feelsLike": f"{now.get('feelsLike', 'N/A')}{temp_unit}",
        "condition": now.get("text", "未知"),
        "icon": now.get("icon", ""),
        "humidity": f"{now.get('humidity', 'N/A')}%",
        "windDir": now.get("windDir", "未知"),
        "windScale": f"{now.get('windScale', 'N/A')}级",
        "windSpeed": f"{now.get('windSpeed', 'N/A')} {speed_unit}",
        "pressure": f"{now.get('pressure', 'N/A')} hPa",
        "visibility": f"{now.get('vis', 'N/A')} km" if UNIT == "m" else f"{now.get('vis', 'N/A')} mi",
        "cloud": f"{now.get('cloud', 'N/A')}%",
        "dew": f"{now.get('dew', 'N/A')}{temp_unit}"
    }


def fetch_forecast(location: str, api_key: str) -> Dict[str, Any]:
    """获取15天天气预报"""
    url = f"{API_BASE_URL}/weather/15d"
    params = {"location": location, "key": api_key, "lang": LANGUAGE, "unit": UNIT}
    data = make_request(url, params)
    
    if not check_response_code(data):
        sys.exit(1)
    
    temp_unit = "°C" if UNIT == "m" else "°F"
    daily = []
    
    for day in data.get("daily", []):
        daily.append({
            "date": day.get("fxDate", ""),
            "tempMax": f"{day.get('tempMax', 'N/A')}{temp_unit}",
            "tempMin": f"{day.get('tempMin', 'N/A')}{temp_unit}",
            "textDay": day.get("textDay", ""),
            "textNight": day.get("textNight", ""),
            "iconDay": day.get("iconDay", ""),
            "iconNight": day.get("iconNight", ""),
            "windDirDay": day.get("windDirDay", ""),
            "windScaleDay": f"{day.get('windScaleDay', 'N/A')}级",
            "humidity": f"{day.get('humidity', 'N/A')}%",
            "precip": f"{day.get('precip', 'N/A')} mm",
            "uvIndex": day.get("uvIndex", "N/A")
        })
    
    return {
        "type": "15天天气预报",
        "updateTime": data.get("updateTime", ""),
        "forecast": daily
    }


def fetch_warning(location: str, api_key: str) -> Dict[str, Any]:
    """获取气象灾害预警"""
    url = f"{API_BASE_URL}/warning/now"
    params = {"location": location, "key": api_key, "lang": LANGUAGE}
    data = make_request(url, params)
    
    if not check_response_code(data):
        sys.exit(1)
    
    warnings = []
    for warning in data.get("warning", []):
        warnings.append({
            "id": warning.get("id", ""),
            "sender": warning.get("sender", ""),
            "pubTime": warning.get("pubTime", ""),
            "title": warning.get("title", ""),
            "severity": warning.get("severity", ""),
            "severityColor": warning.get("severityColor", ""),
            "type": warning.get("type", ""),
            "typeName": warning.get("typeName", ""),
            "text": warning.get("text", "")
        })
    
    return {
        "type": "气象灾害预警",
        "updateTime": data.get("updateTime", ""),
        "warningCount": len(warnings),
        "warnings": warnings if warnings else "当前无预警信息"
    }


def fetch_air_quality(location: str, api_key: str) -> Dict[str, Any]:
    """获取空气质量"""
    # 解析经纬度
    if "," in location:
        lon, lat = location.split(",")
        url = f"{AIR_API_BASE_URL}/current/{lat}/{lon}"
        params = {"lang": LANGUAGE}
    else:
        # 城市ID需要转换为经纬度，这里使用 v7 API
        url = f"{API_BASE_URL}/air/now"
        params = {"location": location, "key": api_key, "lang": LANGUAGE}
        data = make_request(url, params)
        
        if not check_response_code(data):
            sys.exit(1)
        
        now = data.get("now", {})
        return {
            "type": "空气质量",
            "updateTime": data.get("updateTime", ""),
            "aqi": now.get("aqi", "N/A"),
            "level": now.get("level", "N/A"),
            "category": now.get("category", "未知"),
            "primary": now.get("primary", "无"),
            "pm10": now.get("pm10", "N/A"),
            "pm2p5": now.get("pm2p5", "N/A"),
            "no2": now.get("no2", "N/A"),
            "so2": now.get("so2", "N/A"),
            "co": now.get("co", "N/A"),
            "o3": now.get("o3", "N/A")
        }
    
    # 使用空气质量 v1 API（经纬度）
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    indexes = data.get("indexes", {})
    return {
        "type": "空气质量",
        "updateTime": data.get("metadata", {}).get("timestamp", ""),
        "aqi_cn": {
            "aqi": indexes.get("qaqi", {}).get("aqi", "N/A"),
            "level": indexes.get("qaqi", {}).get("level", "N/A"),
            "category": indexes.get("qaqi", {}).get("category", "未知"),
            "color": indexes.get("qaqi", {}).get("color", "")
        },
        "aqi_us": {
            "aqi": indexes.get("us-epa", {}).get("aqi", "N/A"),
            "category": indexes.get("us-epa", {}).get("category", "未知")
        }
    }


def fetch_indices(location: str, api_key: str, indices_types: str = "1,2,3,5,9,16") -> Dict[str, Any]:
    """获取生活指数"""
    url = f"{API_BASE_URL}/indices/1d"
    params = {"location": location, "key": api_key, "lang": LANGUAGE, "type": indices_types}
    data = make_request(url, params)
    
    if not check_response_code(data):
        sys.exit(1)
    
    indices = []
    for item in data.get("daily", []):
        indices.append({
            "type": item.get("type", ""),
            "name": item.get("name", ""),
            "level": item.get("level", ""),
            "category": item.get("category", ""),
            "text": item.get("text", "")
        })
    
    return {
        "type": "生活指数",
        "updateTime": data.get("updateTime", ""),
        "indices": indices
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python get_weather.py <type> <location> [options]", file=sys.stderr)
        print("", file=sys.stderr)
        print("参数:", file=sys.stderr)
        print("  type      查询类型: now(实时), forecast(15天预报), warning(预警), air(空气), indices(指数)", file=sys.stderr)
        print("  location  城市ID（如 101010100）或经纬度（如 116.41,39.92）", file=sys.stderr)
        print("  options   可选参数（仅 indices）: --type 1,2,3", file=sys.stderr)
        print("", file=sys.stderr)
        print("示例:", file=sys.stderr)
        print("  python get_weather.py now 101010100", file=sys.stderr)
        print("  python get_weather.py forecast 116.41,39.92", file=sys.stderr)
        print("  python get_weather.py warning 101010100", file=sys.stderr)
        print("  python get_weather.py air 116.41,39.92", file=sys.stderr)
        print("  python get_weather.py indices 101010100 --type 1,2,3", file=sys.stderr)
        print("", file=sys.stderr)
        print("生活指数类型:", file=sys.stderr)
        for code, name in INDICES_TYPES.items():
            print(f"  {code}: {name}", file=sys.stderr)
        sys.exit(1)
    
    query_type = sys.argv[1].lower()
    location = sys.argv[2]
    api_key = get_api_key()
    
    # 处理生活指数的可选参数
    indices_type = "1,2,3,5,9,16"  # 默认指数
    if query_type == "indices" and len(sys.argv) > 3:
        if sys.argv[3] == "--type" and len(sys.argv) > 4:
            indices_type = sys.argv[4]
    
    # 根据类型调用不同的函数
    handlers = {
        "now": lambda: fetch_now(location, api_key),
        "forecast": lambda: fetch_forecast(location, api_key),
        "warning": lambda: fetch_warning(location, api_key),
        "air": lambda: fetch_air_quality(location, api_key),
        "indices": lambda: fetch_indices(location, api_key, indices_type)
    }
    
    if query_type not in handlers:
        print(f"错误: 不支持的查询类型 '{query_type}'", file=sys.stderr)
        print("支持的类型: now, forecast, warning, air, indices", file=sys.stderr)
        sys.exit(1)
    
    # 获取并输出数据
    result = handlers[query_type]()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
