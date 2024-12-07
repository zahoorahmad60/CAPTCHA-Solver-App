# app.py

import os
import re
import time
import base64
import threading
import shutil
import tempfile
import numpy as np
import cv2
import tensorflow as tf
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from PIL import Image
import undetected_chromedriver as uc
from collections import Counter
from fake_useragent import UserAgent
import urllib3
from urllib3.exceptions import ReadTimeoutError, MaxRetryError, NewConnectionError

app = Flask(__name__)
CORS(app)

def preprocess_image(image, img_width, img_height):
    image_resized = cv2.resize(image, (img_width, img_height))
    gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    morph_img = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel, iterations=2)
    dilated_img = cv2.dilate(morph_img, kernel, iterations=1)
    edges = cv2.Canny(dilated_img, 50, 150)
    return edges / 255.0 

def decode_prediction(pred, num_classes):
    pred_decoded = np.argmax(pred, axis=-1)    
    if pred_decoded.ndim > 1:
        pred_decoded = pred_decoded.flatten()
    return ''.join([str(p) for p in pred_decoded if p < num_classes])

def load_tflite_model(model_path):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter

def tflite_predict(interpreter, input_data):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

def test_single_image(interpreter, img_path, img_width, img_height, num_classes):
    original_image = cv2.imread(img_path)    
    preprocessed_image = preprocess_image(original_image, img_width, img_height)
    X_test = np.array(preprocessed_image).reshape(img_width, img_height, 1)
    X_test = np.expand_dims(X_test, axis=0)
    prediction = tflite_predict(interpreter, X_test.astype(np.float32)) 
    predicted_label = decode_prediction(prediction, num_classes)
    return predicted_label

def captcha_solver(img):
    img_width, img_height = 150, 80
    num_classes = 10
    pred_decoded = test_single_image(interpreter, img, img_width, img_height, num_classes)    
    print(f"Image: {os.path.basename(img)}, Predicted: {pred_decoded}")
    return pred_decoded

def captcha_handler(driver):
    try:
        driver.find_element(By.XPATH, '//h1[contains(text(), "403 Forbidden")]')
        print('Site access denied')
        driver.refresh()
        time.sleep(2)
    except:
        print('Site accessed')

    try:
        driver.find_element(By.XPATH, '//h1[contains(text(), "504 Gateway Time-out")]')
        print('Site access denied')
        driver.refresh()
        time.sleep(2)
    except:
        print('Site accessed')

    try:
        session_ex = driver.find_element(By.XPATH, '//div[contains(text(), "Your session has expired, please login again.")]')
        if session_ex.is_displayed():
            time.sleep(2)
            print('login successfully.....')
            driver.get('https://ita-pak.blsinternational.com/Global/bls/VisaTypeVerification')
    except:
        pass
        
    selected_img = 0
    req_label = ''

    elements = driver.find_elements(By.CSS_SELECTOR,".col-12.box-label")
    
    for element in elements:
        is_visible = driver.execute_script(
            "var elem = arguments[0],                 " +
            "  box = elem.getBoundingClientRect(),    " +
            "  cx = box.left + box.width / 2,         " +
            "  cy = box.top + box.height / 2,         " +
            "  e = document.elementFromPoint(cx, cy); " +
            "for (; e; e = e.parentElement) {         " +
            "  if (e === elem)                        " +
            "    return true;                         " +
            "}                                        " +
            "return false;", element)
        
        if is_visible:
            label_string = element.text
            number = re.search(r'\d+', label_string)
            if number:
                req_label = number.group()
                print('Target:', req_label)
                 
    images = driver.find_elements(By.CSS_SELECTOR, "img.captcha-img")
    
    for index, img in enumerate(images):
        is_visible = driver.execute_script(
            "var elem = arguments[0], box = elem.getBoundingClientRect(), " +
            "cx = box.left + box.width / 2, cy = box.top + box.height / 2, " +
            "e = document.elementFromPoint(cx, cy); for (; e; e = e.parentElement) " +
            "{ if (e === elem) return true; } return false;", img)
    
        if is_visible:
            image_src = img.get_attribute("src")
    
            if image_src.startswith('data:image'):
                base64_data = image_src.split(',')[1]
                image_data = base64.b64decode(base64_data)
                file_ext = 'png'
                file_path = f'captcha_image.{file_ext}'
                
                with open(file_path, 'wb') as handler:
                    handler.write(image_data)
    
                text = captcha_solver(str(file_path))
                os.remove(file_path)
    
                if req_label == text:
                    img.click()
                    selected_img += 1
    
                print(str(file_path), f"contains: {text}")
    if selected_img > 0:
        driver.find_element(By.CSS_SELECTOR, '[onclick="onSubmit();"]').click()
    else:
        driver.find_element(By.CSS_SELECTOR, '[onclick="onReload();"]').click()
        captcha_handler(driver)
        
    try:
        var = driver.switch_to.alert
        Alert(driver).accept()
    except:
        print('No Alert...')

def get_driver():
    os.environ['SSL_CERT_FILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cacert.pem')
    options = uc.ChromeOptions()
    # Commenting out headless for debugging; re-enable after troubleshooting if desired
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')

    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')

    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(300)
    driver.delete_all_cookies()
    return driver

interpreter = load_tflite_model("Final Model (1)/Final Model/Testimg/Capmodel_098613.tflite")
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

driver = get_driver()

book_appointment_link = 'https://pakistan.blsspainglobal.com/Global/account/login'

max_retries = 3
for attempt in range(max_retries):
    try:
        driver.get(book_appointment_link)
        print(f"Successfully loaded {book_appointment_link}")
        break
    except (WebDriverException, ReadTimeoutError, TimeoutException) as e:
        print(f"Attempt {attempt + 1} to load the page failed: {e}")
        if attempt == max_retries - 1:
            print("Max retries reached. Exiting.")
            driver.quit()
            driver = None

def run_captcha():
    if not driver:
        print("Driver is not initialized. Cannot run captcha.")
        return
    while True:
        try:
            try:
                captcha_frame = driver.find_element(By.CSS_SELECTOR, '[title="Verify Registration"]')
            except NoSuchElementException:
                try:
                    captcha_frame = driver.find_element(By.CSS_SELECTOR, '[title="Verify Selection"]')
                except NoSuchElementException:
                    captcha_frame = driver.find_element(By.CSS_SELECTOR, '[title="Verify Appointment"]')
            
            driver.switch_to.frame(captcha_frame)
            captcha_handler(driver)
            driver.switch_to.default_content()
        
        except Exception as e:
            driver.switch_to.default_content()
            print('No captcha found......')
            time.sleep(1)
            continue
        
        try:
            var = driver.switch_to.alert
            Alert(driver).accept()
        except:
            print('No Alert...')
        
        try:
            if driver.find_element(By.CSS_SELECTOR, '#btnVerified').is_displayed():
                print('User verified successfully...')
                break
        except:
            pass
        
        time.sleep(2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_captcha():
    if not driver:
        return jsonify({'error': 'WebDriver is not initialized.'}), 500
    thread = threading.Thread(target=run_captcha)
    thread.start()
    return jsonify({'message': 'CAPTCHA solving started.'}), 200

@app.route('/stop', methods=['POST'])
def stop_captcha():
    global stop_event, captcha_thread
    if not captcha_thread or not captcha_thread.is_alive():
        return jsonify({'error': 'No CAPTCHA-solving process is currently running.'}), 400

    stop_event.set()  # Signal the thread to stop
    captcha_thread.join()  # Wait for the thread to terminate
    captcha_thread = None  # Reset the thread variable
    return jsonify({'message': 'CAPTCHA solving stopped.'}), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
