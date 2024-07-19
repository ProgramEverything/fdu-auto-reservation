import requests
import json


def nn_service_request(
        verifyPicWithCharTarget_base64: str,
        api_name: str = 'clickOn'
):
    requestBody = json.dumps({
        "dataType": 2,
        "imageSource": verifyPicWithCharTarget_base64
    })
    raw_result = requests.post(
        "http://127.0.0.1:8000/{}".format(api_name),
        data=requestBody
    )   # 为什么这里的请求体是传给data形参，而不是json形参？？
    assert raw_result.status_code == 200, "返回错误码：{}".format(raw_result.status_code)
    recog_result = json.loads(raw_result.content.decode("utf-8"))
    return recog_result['data']['res']