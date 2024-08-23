import os
import openai
import PyPDF2

openai.organization = "org-gHCQMnFoSOdsWuYcdbnuHPYR"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()



print(openai.api_key)

pdf_summary_text = ""

pdf_file_path = "/Users/simoninnes/Documents/Explore/Papers/Machine Learning/Dual Approach to Modeling.pdf"

pdf_file = open(pdf_file_path, 'rb')

pdf_reader = PyPDF2.PdfReader(pdf_file)

for page_num in range(len(pdf_reader.pages)):

    page_text = pdf_reader.pages[page_num].extract_text().lower()


# Call openai model

response = openai.ChatCompletion.create(

   model="gpt-3.5-turbo",

   messages=[

      {"role": "system", "content": "You are a helpful research assistant."},

      {"role": "user", "content": f"Summarize this: {page_text}"},

   ],

)

page_summary = response["choices"][0]["message"]["content"]


# Save summary pdf
pdf_summary_text += page_summary + "\n"

pdf_summary_file = pdf_file_path.replace(os.path.splitext(pdf_file_path)[1], "_summary.txt")

with open(pdf_summary_file, "w+") as file:

   file.write(pdf_summary_text)
