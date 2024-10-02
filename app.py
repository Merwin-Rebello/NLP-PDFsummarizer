from flask import Flask, request, render_template, redirect, url_for
import PyPDF2
import spacy
from heapq import nlargest
from string import punctuation

app = Flask(__name__)

# Function to clean and extract relevant text from PDF
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    
    # Start the text from the abstract section
    abstract_start = text.lower().find("abstract")
    if abstract_start != -1:
        text = text[abstract_start:]
    
    return text

# Function to preprocess and summarize text
def summarize(text, num_sentences=3):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)

    # Tokenize text and remove stop words, punctuation, and irrelevant tokens
    stopwords = list(spacy.lang.en.stop_words.STOP_WORDS)
    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in stopwords and word.text.lower() not in punctuation and not word.is_space:
            if word.text.lower() not in word_frequencies:
                word_frequencies[word.text.lower()] = 1
            else:
                word_frequencies[word.text.lower()] += 1

    # Get max frequency
    max_freq = max(word_frequencies.values())

    # Normalize frequencies
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_freq

    # Score sentences by word frequencies
    sentence_scores = {}
    for sent in doc.sents:
        for word in sent:
            if word.text.lower() in word_frequencies:
                if sent not in sentence_scores:
                    sentence_scores[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]

    # Dynamically adjust the number of summary sentences based on text length
    num_sentences = max(3, int(len(list(doc.sents)) * 0.1))  # Use 10% of total sentences, at least 3

    # Select the best sentences
    summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    summary = ' '.join([sent.text for sent in summary_sentences])

    return summary

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = ''
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            # Extract text from the uploaded PDF file
            text = extract_text_from_pdf(file)

            # Summarize the extracted text
            summary = summarize(text)

    return render_template('index.html', summary=summary)

if __name__ == '__main__':
    app.run(debug=True)
