import os
import base64
from flask import Flask, request, jsonify
from selenium import webdriver
from flask_cors import CORS
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Chrome options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize the WebDriver in headless mode
driver = webdriver.Chrome(options=chrome_options)

@app.route('/solve_captcha', methods=['POST'])
def solve_captcha():
    # Get the image data from the POST request
    data = request.json
    base64_image = data['captcha_image']

    # Convert base64 image to a PNG file
    image_file_path = "captcha.png"
    with open(image_file_path, "wb") as fh:
        fh.write(base64.b64decode(base64_image.split(',')[1]))
    print(f"Image saved as '{image_file_path}'")

    # Open Google Lens in the browser
    driver.get("https://lens.google.com/?hl=en")
    wait = WebDriverWait(driver, 30)

    try:
        # Wait for the drag-and-drop area to become visible
        drag_and_drop_area = wait.until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div[2]/c-wiz/div[2]/div/div[3]/div[2]'))
        )
        
        # Read the captcha file as a binary string
        with open(image_file_path, 'rb') as image_file:
            image_data = image_file.read()

        # Simulate drag-and-drop to upload the image to Google Lens
        js_script = """
        var dropArea = arguments[0];
        var fileName = arguments[1];
        var contentType = arguments[2];
        var fileContent = new Uint8Array(arguments[3]);
        
        var file = new File([fileContent], fileName, {type: contentType});
        var dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        var event = new DragEvent('drop', {
            dataTransfer: dataTransfer,
            bubbles: true,
            cancelable: true
        });
        dropArea.dispatchEvent(event);
        """
        driver.execute_script(js_script, drag_and_drop_area, os.path.basename(image_file_path), 'image/png', list(image_data))

        # Wait for Google Lens to process the image and return the result
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/c-wiz/div/div[2]/div/c-wiz/div/div[1]/div/div[3]/div/div/span[2]/span/button/span[1]'))).click()

        try:
            recognized_text_element = wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/c-wiz/div/div[2]/div/c-wiz/div/div[2]/c-wiz/div/div/span/div/h1'))
            )
            recognized_text = recognized_text_element.text.strip().lower()
            print("Extracted Text from Google Lens:", recognized_text)
            return jsonify({"text": recognized_text})
        except:
            return jsonify({"text": "No text found"})
    except Exception as e:
        print("Error:", e)
        return jsonify({"text": "", "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
