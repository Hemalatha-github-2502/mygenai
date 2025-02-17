from flask import Flask, request, render_template_string,send_file
import os
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import textwrap
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
 
def generate_pdf(text):
    # Create an in-memory buffer for the PDF
    buffer = io.BytesIO()
   
    # Create the PDF canvas using letter page size
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 10)
   
    # Define margins and line height
    left_margin = 72      # 1 inch from the left
    top_margin = letter[1] - 72  # 1 inch from the top
    bottom_margin = 72    # 1 inch from the bottom
    line_height = 12      # Space between lines
 
    # Prepare the text by wrapping each line
    wrapped_lines = []
    wrap_width = 90  # Adjust as needed based on your font and page width
    for line in text.split("\n"):
        # If a line is empty, add an empty string to preserve line breaks
        if not line.strip():
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(textwrap.wrap(line, width=wrap_width))
   
    # Start writing from the top margin
    y = top_margin
 
    # Write each line to the PDF and add a new page if needed
    for line in wrapped_lines:
        # If y is below the bottom margin, add a new page
        if y < bottom_margin:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = top_margin  # Reset y to top of new page
 
        pdf.drawString(left_margin, y, line)
        y -= line_height  # Move down for the next line
 
    pdf.save()
    buffer.seek(0)
   
    return send_file(buffer, as_attachment=True, download_name="result.pdf", mimetype="application/pdf")
 
# Load environment variables
load_dotenv()
 
# Configure the model
model = genai.GenerativeModel("gemini-pro")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
 
app = Flask(__name__)
 
# Define the prompt template
prompt_template = """
You are a highly skilled code review bot. You will be given a code snippet along with user instruction if any. Follow the below instructions to analyze the code and provide detailed review as follows:
1. **Do not change the actual logic of the code.**
 
2. **Provide a detailed review:**
   
     * **Code Name:** The name of the code snippet or file.
     * **Optimized Files:** The number of files that could be optimized.
     * **File Type:** The type of the file (e.g., Python, JavaScript).
     * **Review Comment:** A concise description of the issue or improvement suggestion.
     * **Reason for Review:** A more detailed explanation of why the review is necessary.
 
3. **Analyze the code:**
   * Create a tabular output with the following columns:
     * Syntax errors
     * Logical errors
     * Ambiguous column names
     * Aggregated columns
     * Redundant code
     * Style issues
     * Code's readability
     * Maintainability
     * Efficiency
 
4. **Provide an optimized code snippet:**
   * If applicable, offer a revised version of the code that incorporates the suggested improvements.
   * Ensure the optimized code maintains the original functionality and meets the specified requirements.
   * Create a tabular output comparison of original code and the optimized code.
 
 
. **Suggest improvements for best practices:**
   * Propose specific changes to enhance the code's quality, performance, or readability.
   * Refer to relevant coding standards, best practices, or design patterns.
 
 
Do not affect the actual code and don't change the business transformations logic unless any instruction is given to modify the actual code logic.
 
Below is the code:
**Code:**
{code}
 
Follow up with the user for further instructions.
{message}.
"""
review_result=""
 
 
@app.route('/', methods=['GET', 'POST'])
def index():
    global review_result
    review_result=""
    review_response = None
    input_code = ""
 
    if request.method == 'POST':
        input_code = request.form['code']
        prompt = prompt_template.format(code=input_code, message="Provide a detailed review.")
        response = model.generate_content(prompt)
        review_result = response.text
 
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Code Review</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f4f4; text-align: center; padding: 20px; }
                .container { width: 60%; margin: auto; background: white; padding: 20px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.2); border-radius: 10px; }
                textarea { width: 100%; height: 200px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; resize: none; }
                button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 10px; }
                button:hover { background-color: #0056b3; }
                .response-container { margin-top: 20px; text-align: left; padding: 15px; background: #e8f0fe; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1); }
                pre { white-space: pre-wrap; word-wrap: break-word; background: #f8f9fa; padding: 10px; border-radius: 5px; }
            </style>
        </head>
        <body>
 
            <div class="container">
                <h1>AI Code Review</h1>
                <form method="post">
                    <label for="code">Enter your code:</label>
                    <textarea name="code" id="code">{{ input_code }}</textarea>
                    <br>
                    <button type="submit">Review Code</button>
                </form>
 
                {% if review_result %}
                <div class="response-container">
                    <h2>Code Review Result</h2>
                    <pre>{{ review_result }}</pre>
                    <a href="/download" target="_blank">
                        <button>Download as PDF</button>
                    </a>
                </div>
                {% endif %}
            </div>
 
        </body>
        </html>
    """, input_code=input_code, review_result=review_result)
 
@app.route('/download')
def download_pdf():
    global review_result  # Assume review_result contains your full result text
    if not review_result:
        return "No review result found!", 400
    return generate_pdf(review_result)
 
if __name__ == '__main__':
    app.run(debug=True)