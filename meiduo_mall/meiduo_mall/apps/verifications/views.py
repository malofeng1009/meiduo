import random

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from meiduo_mall.libs.captcha.captcha import captcha
from verifications import serializers
from .import constants


class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        """
        获取图片验证码
        """

        # 生成验证码图片
        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    serializer_class = serializers.CheckImageCodeSerializer

    def get(self, request, mobile):
        # 校验图片验证码和发送短信的次数

        # mobile 是被放到了类视图对象属性kwargs中
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 校验通过
        # 生成短信验证码发送记录
        sms_code = '%06d' % random.randint(0, 999999)

        print('短信验证码：' + sms_code)

        # 保存验证码及发送记录
        redis_conn = get_redis_connection('verify_codes')

        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 使用 redis 的pipeline 管道一次执行多个命令
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 让管道执行命令
        pl.execute()

        # 发送短信
        # ccp = ccp()
        # time = str(constants.IMAGE_CODE_REDIS_EXPIRES / 60)
        # ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
        #使用 celery 发布异步任务
        result = send_sms_code.delay(mobile, sms_code)

        # 返回
        return Response({'message':'OK'})

