import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer

# ตั้งชื่อแอป
st.title("Plasma Bag Color Classification")
st.write("ถ่ายภาพถุงน้ำเหลืองเพื่อตรวจสอบสี (Acceptable/Unacceptable)")

# ฟังก์ชันสำหรับการตรวจสอบสี
def classify_plasma_color(image):
    # แปลงภาพจาก PIL เป็น NumPy Array
    np_image = np.array(image)
    
    # แปลงภาพจาก RGB เป็น BGR (สำหรับ OpenCV)
    bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

    # แปลงภาพจาก BGR เป็น HSV
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

    # กำหนดขอบเขตของสี Acceptable (ตัวอย่างสีเหลือง)
    lower_bound = np.array([20, 100, 100])  # ค่าต่ำสุดของสี
    upper_bound = np.array([40, 255, 255])  # ค่าสูงสุดของสี

    # สร้าง Mask สำหรับพื้นที่ที่อยู่ในขอบเขตสี
    mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

    # คำนวณเปอร์เซ็นต์พื้นที่ที่ตรงกับสี Acceptable
    total_pixels = mask.size
    acceptable_pixels = cv2.countNonZero(mask)
    percentage = (acceptable_pixels / total_pixels) * 100

    # เงื่อนไขสำหรับการตัดสินผล
    if percentage > 20:  # กำหนด 20% เป็นเกณฑ์ขั้นต่ำ
        classification = "Acceptable"
    else:
        classification = "Unacceptable"

    # สร้างผลลัพธ์เป็นภาพ
    result_image = cv2.bitwise_and(bgr_image, bgr_image, mask=mask)

    return classification, result_image

# คลาสสำหรับ WebRTC
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.result_image = None
        self.classification = None

    def recv(self, frame):
        # รับภาพจากกล้อง
        img = frame.to_ndarray(format="bgr24")
        
        # แปลงภาพเป็น RGB และใช้ฟังก์ชัน classify_plasma_color
        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        self.classification, self.result_image = classify_plasma_color(pil_image)
        
        # คืนผลลัพธ์เป็นภาพ BGR
        return av.VideoFrame.from_ndarray(self.result_image, format="bgr24")

# ส่วนสำหรับเปิดใช้งานกล้อง
ctx = webrtc_streamer(key="example", video_processor_factory=VideoProcessor)

# แสดงผลลัพธ์จากกล้อง
if ctx.video_processor:
    st.write("**ผลลัพธ์:**")
    st.write(f"สถานะ: {ctx.video_processor.classification}")
    if ctx.video_processor.result_image is not None:
        st.image(ctx.video_processor.result_image, caption="ผลลัพธ์การตรวจสอบสี", use_column_width=True)
