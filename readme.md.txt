# DeloitteSmartApp

An AI-powered Streamlit application that helps users analyze and summarize documents using OCR and OpenAI GPT models. Designed for use cases like M\&A support, subsidy documentation, and executive reporting.

---

## 🚀 Features

* 📸 OCR image capture or upload for text extraction
* 📄 PDF and TXT document upload and auto-summarization
* 💬 Chat interface to query content using GPT-3.5
* 📥 Downloadable executive summary report
* 🌐 Language toggle: English / Japanese

---

## 📁 Project Structure

```
DeloitteSmartApp/
├── app.py                  # Main Streamlit app
├── app/
│   ├── __init__.py
│   ├── ocr_utils.py       # OCR logic using pytesseract
│   ├── gpt_utils.py       # Summarization and report generation
│   └── ui_utils.py        # Language and session management
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```

---

## 🛠️ Installation

1. **Clone this repository**:

   ```bash
   git clone https://github.com/your-username/DeloitteSmartApp.git
   cd DeloitteSmartApp
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure Tesseract OCR is installed** on your system.

   * [Install Tesseract](https://github.com/tesseract-ocr/tesseract/wiki)
   * Update the path in `ocr_utils.py` if needed:

     ```python
     pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
     ```

---

## ▶️ Run the App

```bash
streamlit run app.py
```

---

## 📸 Screenshots

> *You can add screenshots of the app interface here.*

---

## 📝 License

MIT License. See `LICENSE` file for details.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss.
