from django.shortcuts import render
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import fitz  # PyMuPDF
import cohere

from django.conf import settings

COHERE_API_KEY = settings.COHERE_API_KEY

# Home & Static Pages
def home(request):
    return render(request, 'core/home.html')

def notes(request):
    return render(request, 'core/notes.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def terms(request):
    return render(request, 'core/terms.html')

def all_in_one_ai(request):
    return render(request, 'core/all-in-one-ai.html')


MODEL_MAP = {
    "chatgpt-response": "command-r-plus-04-2024",
    "copilot-response": "command-r-08-2024",
    "backbox-response": "command-light",
    "gemini-response": "command-light-nightly"
}


from django.views.decorators.http import require_POST
import requests

@csrf_exempt
@require_POST
def get_ai_responses(request):
    try:
        body = json.loads(request.body)
        prompt = body.get("prompt", "")
        results = {}

        for response_id, model in MODEL_MAP.items():
            cohere_response = requests.post(
                "https://api.cohere.ai/v1/generate",
                headers={
                    "Authorization": f"Bearer {COHERE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "prompt": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            response_data = cohere_response.json()
            results[response_id] = response_data.get("generations", [{}])[0].get("text", "No response.")

        return JsonResponse(results)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def login(request):
    return render(request, 'core/login.html')
def signup(request):
    return render(request, 'core/signup.html')
def logout(request):
    return render(request, 'core/logout.html')

# Cohere API Setup
co = cohere.Client(COHERE_API_KEY)

def extract_text_from_pdf(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text


def generate_mcqs_cohere(text):
    prompt = (
        "Generate 10 multiple-choice questions (MCQs) from the following text. "
        "Each question should have 4 answer choices, with one correct option clearly marked. "
        "Format: Question -> Option A, Option B, Option C, Option D | Correct Answer: X\n\n"
        "Make sure to add answers of the all the questions you created"
        f"{text}"
    )
    response = co.generate(
        model="command-r-plus-04-2024",
        prompt=prompt,
        max_tokens=1000000000,
        temperature=0.7,
    )
    return response.generations[0].text

def clean_text(text):
    return re.sub(r'\n+', '\n', text.strip())

# MCQ Generator
def mcq_generator(request):
    if request.method == "POST" and request.FILES.get("pdf"):
        pdf_file = request.FILES["pdf"]
        text = extract_text_from_pdf(pdf_file.read())
        mcqs = generate_mcqs_cohere(text)
        return JsonResponse({"mcqs": mcqs})
    return render(request, "core/mcq-generator.html")


# Chat with PDF Upload
def chat_with_pdf(request):
    if request.method == "POST" and request.FILES.get("pdf"):
        pdf_file = request.FILES["pdf"]
        text = extract_text_from_pdf(pdf_file.read())
        clean = clean_text(text)
        request.session['pdf_context'] = clean
        return JsonResponse({"message": "PDF uploaded successfully", "file_name": pdf_file.name})
    return render(request, "core/chat-with-pdf.html")

# Chat with PDF - Ask Question
@csrf_exempt
def chat_with_pdf_ask(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            question = body.get("question", "")
            context = request.session.get("pdf_context", "")

            if not context:
                return JsonResponse({"answer": "Please upload a PDF first."}, status=400)

            prompt = (
                "You are an AI assistant that reads the following document and answers questions ONLY based on it.\n"
                f"Document:\n{context}\n\n"
                f"User Question:\n{question}\n\n"
                "Answer (based ONLY on the document above):"
            )

            response = co.generate(
                model="command-r-plus-04-2024",
                prompt=prompt,
                max_tokens=10000000,
                temperature=0.7,
            )

            answer = response.generations[0].text.strip()
            return JsonResponse({"answer": answer})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method."}, status=400)

# Optional: Alternate generic chat endpoint
@csrf_exempt
def chat_query(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question")
        context = data.get("context")

        prompt = (
            f"You are a helpful assistant. Based on the following PDF content, answer the user's question:\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\nAnswer:"
        )

        response = co.generate(
            model="command-r-03-2024",
            prompt=prompt,
            max_tokens=300,
            temperature=0.5,
        )

        answer = response.generations[0].text.strip()
        return JsonResponse({"answer": answer})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages

# Existing views (leave unchanged)...

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'core/login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'core/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'core/signup.html')

        user = User.objects.create_user(username=username, password=password)
        auth_login(request, user)
        return redirect('home')

    return render(request, 'core/signup.html')


def logout(request):
    auth_logout(request)
    return redirect('home')


from django.contrib.auth.decorators import login_required
from .models import Note
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from .models import Note
from django.contrib.auth.decorators import login_required


@login_required
def notes(request):
    user_notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/notes.html', {'notes': user_notes})

@csrf_exempt
@login_required
def save_note(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if title and content:
            Note.objects.create(user=request.user, title=title, content=content)
    return redirect('notes')


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    return redirect('notes')

@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.content = request.POST.get('content')
        note.save()
        return redirect('notes')
    return render(request, 'core/edit_note.html', {'note': note})
