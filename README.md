# CAPTCHA Solver Flask Server

This repository provides a Flask-based server that automatically solves image-based CAPTCHAs on a target website. The application integrates a pre-trained TensorFlow Lite model for CAPTCHA recognition with Selenium WebDriver for navigating and interacting with the webpage. By running this server, you can programmatically solve CAPTCHAs and handle session renewals without manual intervention.

---

## Key Features

- **Automated CAPTCHA Solving**: Utilizes a TensorFlow Lite (TFLite) model to recognize and solve CAPTCHAs on-the-fly.
- **Web Automation with Selenium**: Uses undetected_chromedriver to navigate the target website, handle frames, and manage form submissions.
- **Headless Mode**: Can run in headless mode for deployment on servers without GUIs (e.g., cloud environments or Docker containers).
- **Configurable and Extensible**: Easy to modify input dimensions, model paths, target URLs, and other parameters.
- **RESTful API**: Provides a simple HTTP endpoint (`/start`) to initiate the CAPTCHA-solving process.

---

## How It Works

1. **Model Loading**: A pre-trained TFLite model is loaded at startup. This model takes an image of the CAPTCHA, preprocesses it, and predicts the CAPTCHA text.
2. **Web Navigation**: Selenium with undetected_chromedriver launches a Chrome browser, navigates to the specified target website, and waits for the CAPTCHA frame.
3. **CAPTCHA Extraction**: The CAPTCHA image is extracted from the webpage, converted from Base64 to an image file, and passed to the model for prediction.
4. **Interaction**: Once the CAPTCHA text is identified, the script selects the correct image (if applicable) or enters the predicted text, then submits.
5. **Continuous Monitoring**: The server repeatedly checks for new CAPTCHAs or session expirations and solves them automatically as they appear.

---

## Project Structure

```
.
├── app.py                 # Main Flask application code
├── templates/
│   └── index.html         # Simple front-end page to trigger CAPTCHA solving
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration for containerized deployment
└── README.md              # Project documentation (this file)
```

---

## Requirements

- **Python**: 3.10 or above recommended.
- **TensorFlow Lite**: For loading and running the pre-trained TFLite model.
- **OpenCV**: For image preprocessing.
- **Selenium & undetected_chromedriver**: For browser automation.
- **Flask & flask-cors**: For running the web server and handling CORS.
- **Tesseract (Optional)**: If you plan to integrate with OCR solutions (already included in Docker setup).

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **Set Up a Virtual Environment** (Highly recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   
   The `requirements.txt` includes packages like:
   - `Flask`, `flask-cors`
   - `tensorflow`, `opencv-python`
   - `selenium`, `undetected-chromedriver`
   - `Pillow`, `fake-useragent`
   - `requests`, `certifi`

4. **Download or Provide Model File**:
   - Ensure you have the TFLite model file (`Capmodel_098613.tflite` or a similar model) in the correct path.  
   - Update `backend_server.py` with the correct model file path if you have placed it elsewhere:
     ```python
     interpreter = load_tflite_model("path/to/your_model.tflite")
     ```

---

## Running the Application

1. **Start the Flask Server**:
   ```bash
   python backend_server.py
   ```
   
   By default, the server runs on `http://0.0.0.0:5000`.

2. **Access the Main Page**:
   - Open a browser and navigate to `http://localhost:5000` (or the server’s IP if remote).
   - You should see a simple interface with a button to start CAPTCHA solving.

3. **Trigger CAPTCHA Solving**:
   - Click the **"Start CAPTCHA Solving"** button on the page.
   - The server will begin navigating to the specified website and attempt to solve any CAPTCHAs it encounters automatically.

---

## Using the API

- **Endpoint**: `/start`
  
  **Method**: `POST`
  
  **Description**: Initiates the CAPTCHA solving thread.

  **Example**:
  ```bash
  curl -X POST http://localhost:5000/start -H "Content-Type: application/json" -d '{}'
  ```

  **Response**:
  ```json
  {
    "message": "CAPTCHA solving started."
  }
  ```

---

## Docker Deployment

1. **Build the Docker Image**:
   ```bash
   docker build -t captcha_solver_flask .
   ```

2. **Run the Container**:
   ```bash
   docker run -d -p 5000:5000 captcha_solver_flask
   ```

3. **Access the App**:
   - Visit `http://localhost:5000` (or the server’s IP) to access the Flask server.

**Note**: The Dockerfile includes installation of all necessary dependencies, including Tesseract OCR for completeness.

---

## Troubleshooting

- **Connection Timeouts**:  
  If Selenium times out accessing the target website:
  - Check internet connectivity.
  - Verify the target URL.
  - Increase `set_page_load_timeout` in `get_driver()` function in `app.py`.

- **CAPTCHA Not Being Solved**:  
  If the CAPTCHA isn’t recognized:
  - Confirm that the model file path is correct.
  - Adjust preprocessing parameters in `preprocess_image`.
  - Ensure the TFLite model is trained correctly and supports the detected CAPTCHA type.

- **Selenium / ChromeDriver Issues**:  
  If Chrome fails to launch:
  - Ensure Google Chrome is installed.
  - Update `undetected-chromedriver`.
  - Temporarily remove `--headless` mode to debug visually.

---

## Customization

- **Model Path**: Update `interpreter = load_tflite_model("...")` in `backend_server.py`.
- **Target URL**: Change `book_appointment_link` in `app.py` to point to the desired website.
- **User-Agent Rotation**: The code uses `fake-useragent` to randomize the User-Agent. You can disable or specify a custom user-agent by modifying `get_driver()` function.
- **CORS Configuration**: Adjust `CORS(app)` in `app.py` if you need different CORS settings.

---

## Security Considerations

- **Authentication**: If exposing the server publicly, consider adding authentication or rate limiting on the `/start` endpoint.
- **HTTPS**: Use a reverse proxy (e.g., Nginx, Traefik) with TLS certificates in production for secure communication.
- **Prevent Abuse**: This tool can be used to bypass CAPTCHA challenges. Ensure compliance with the target website’s terms of service and legal regulations before deployment.

---

## License

This project is licensed under the MIT License. See the [LICENSE](zah4922@gmail.com) file for details.

---

## Acknowledgments

- **TensorFlow** and **OpenCV** for their robust ML and image processing capabilities.
- **Selenium** and **undetected_chromedriver** for enabling headless browser automation.
- **Flask** for providing a simple and lightweight web server framework.
- **fake-useragent**, **pytesseract**, and other open-source tools used in this project.

**Thank you for using the CAPTCHA Solver Flask Server!**
