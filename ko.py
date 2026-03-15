import google.generativeai as genai

genai.configure(api_key="AIzaSyA5v72cFKYlWw9dz6rfMVrrYfh9EMLKhmI")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)# cook your dish here
