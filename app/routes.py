from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import JournalEntry, User
from openai import AzureOpenAI
import os
from textblob import TextBlob
import re

def get_detailed_sentiment(text):
    # Step 1: Data Preprocessing
    # Remove URLs, special characters, and convert to lowercase
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    
    # Step 2: Sentiment Analysis with TextBlob
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Step 3: Enhanced Emotion Detection
    # Define emotional keywords
    anxiety_words = ['anxious', 'anxiety', 'worried', 'nervous', 'stress', 'stressed', 'panic', 'fear', 'uneasy', 'restless']
    confusion_words = ['confused', 'unsure', 'uncertain', 'lost', 'puzzled', 'bewildered', 'dont know', "don't know", 'unclear']
    negative_words = ['sad', 'bad', 'hard', 'difficult', 'struggle', 'overwhelm']
    positive_words = ['good', 'happy', 'great', 'wonderful', 'excited', 'joy', 'hopeful', 'optimistic']
    
    # Check for presence of emotional keywords
    has_anxiety = any(word in text for word in anxiety_words)
    has_confusion = any(word in text for word in confusion_words)
    has_negative = any(word in text for word in negative_words)
    has_positive = any(word in text for word in positive_words)
    
    # Step 4: Enhanced Sentiment Categorization
    emotions = []
    if has_anxiety:
        emotions.append("Anxious/Stressed")
    if has_confusion:
        emotions.append("Confused/Uncertain")
    
    # Determine primary sentiment
    if polarity <= -0.3:
        sentiment = "Strongly Negative"
        if has_anxiety and has_confusion:
            description = "The text expresses strong anxiety and confusion, indicating a challenging emotional state."
        elif has_anxiety:
            description = "The text shows significant anxiety and stress, with strong negative emotions."
        elif has_confusion:
            description = "The text reveals deep confusion and uncertainty, with strong negative feelings."
        else:
            description = "The text expresses strong negative emotions and concerns."
    elif polarity <= -0.1:
        sentiment = "Negative"
        if has_anxiety and has_confusion:
            description = "The text indicates both anxiety and confusion, suggesting emotional uncertainty."
        elif has_anxiety:
            description = "The text shows signs of anxiety and stress."
        elif has_confusion:
            description = "The text expresses confusion and uncertainty."
        else:
            description = "The text shows negative emotions and worries."
    elif polarity <= 0.1:
        if has_anxiety or has_confusion:
            sentiment = "Mixed with Anxiety/Confusion"
            if has_anxiety and has_confusion:
                description = "While neutral in tone, the text expresses both anxiety and confusion."
            elif has_anxiety:
                description = "Despite a neutral tone, the text indicates underlying anxiety."
            else:
                description = "The text shows confusion despite its neutral tone."
        elif has_negative and not has_positive:
            sentiment = "Negative"
            description = "The text shows signs of negative emotions despite the neutral tone."
        elif has_positive and not has_negative:
            sentiment = "Positive"
            description = "The text shows signs of positive emotions despite the neutral tone."
        else:
            sentiment = "Neutral"
            description = "The text has a balanced tone with mixed emotions."
    elif polarity <= 0.3:
        sentiment = "Positive"
        if has_anxiety or has_confusion:
            description = "Despite positive elements, there are signs of underlying anxiety or uncertainty."
        else:
            description = "The text shows positive aspects and hopeful elements."
    else:
        sentiment = "Strongly Positive"
        if has_anxiety or has_confusion:
            description = "While very positive, there are hints of underlying anxiety or uncertainty."
        else:
            description = "The text expresses strong positive emotions and optimism."
    
    # Step 5: Subjectivity Analysis
    if subjectivity > 0.7:
        subjectivity_level = "Highly Subjective"
        subjectivity_desc = "The text is very personal and emotionally charged."
    elif subjectivity > 0.4:
        subjectivity_level = "Moderately Subjective"
        subjectivity_desc = "The text shows a mix of personal feelings and objective observations."
    else:
        subjectivity_level = "More Objective"
        subjectivity_desc = "The text maintains a relatively objective perspective."
    
    # Step 6: Return Comprehensive Analysis
    return {
        "sentiment": sentiment,
        "description": description,
        "emotions": emotions,  # New field for specific emotions detected
        "subjectivity": subjectivity_level,
        "subjectivity_desc": subjectivity_desc,
        "polarity": round(polarity, 2),
        "subjectivity_score": round(subjectivity, 2)
    }

def analyze_entry(text):
    # Get detailed sentiment analysis
    sentiment_analysis = get_detailed_sentiment(text)

    # Get AI insights using Azure OpenAI
    try:
        # Initialize Azure OpenAI client with proper error handling
        if not all([
            os.getenv("AZURE_OPENAI_API_KEY"),
            os.getenv("AZURE_OPENAI_API_VERSION"),
            os.getenv("AZURE_OPENAI_ENDPOINT"),
            os.getenv("AZURE_OPENAI_DEPLOYMENT")
        ]):
            raise ValueError("Missing required Azure OpenAI environment variables")

        # Initialize client with only the required parameters
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": """You are ReflectAI, an emotionally intelligent journaling companion. Your role is to provide deeply personalized and validating analysis that helps users process their experiences. When analyzing a journal entry:

1. Emotional Resonance
- Start by directly acknowledging the specific emotions expressed
- Use phrases like "I hear you feeling..." or "It sounds like you're experiencing..."
- Validate the intensity and complexity of their emotions
- Avoid generic phrases like "it's common to feel" or "many people experience"

2. Contextual Understanding
- Identify specific triggers or situations mentioned
- Note any patterns in their emotional experience
- Recognize how their current state affects their daily life
- Acknowledge the impact on their motivation and energy

3. Personalized Support
- Offer one specific, actionable suggestion that directly relates to their situation
- Provide a gentle reframing that acknowledges their struggle while offering hope
- Include a thoughtful journaling prompt that encourages deeper exploration
- End with a validating statement that shows you understand their experience

Example Response Structure:
"I hear you feeling [specific emotion] about [specific situation]. The way you describe [specific detail] shows how deeply this is affecting you. When motivation feels heavy and tasks seem overwhelming, it can be especially challenging to [specific challenge they mentioned]. 

One small step you might consider is [specific, personalized suggestion]. This could help you [specific benefit].

For deeper reflection, you might explore: [thoughtful journaling prompt]

Remember, it's okay to feel this way, and your experience is valid. Would you like to explore any particular aspect of this further?"

Use a warm, conversational tone throughout. Focus on making the writer feel truly heard and understood."""},
                {"role": "user", "content": text}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        analysis = response.choices[0].message.content
    except Exception as e:
        # Only print error if it's not the proxies error
        if "proxies" not in str(e):
            print(f"Azure OpenAI Error: {str(e)}")
        
        sentiment = sentiment_analysis['sentiment']
        description = sentiment_analysis['description']
        
        # More personalized fallback response based on sentiment
        if sentiment in ["Strongly Positive", "Positive"]:
            analysis = (
                f"I notice you're feeling {sentiment.lower()}. {description} "
                "That's wonderful to hear! Take a moment to enjoy this feeling and reflect on what contributed to it. "
                "You might consider: What helped you feel this way today? How can you invite more of this into your routine?"
            )
        elif sentiment in ["Strongly Negative", "Negative"]:
            analysis = (
                f"I notice you're feeling {sentiment.lower()}. {description} "
                "It's okay to sit with these emotions. They can be tough, but acknowledging them is a step toward understanding. "
                "Consider: What do you need most right now to support yourself?"
            )
        else:
            analysis = (
                f"I notice your entry has a {sentiment.lower()} tone. {description} "
                "If you're not sure how you're feeling, that's okay too. Writing things down is already a good start. "
                "Try exploring: Is there something weighing on your mind, or something you're trying to figure out?"
            )
    
    return {
        "sentiment_analysis": sentiment_analysis,
        "analysis": analysis
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit_entry', methods=['POST'])
@login_required
def submit_entry():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({
                "error": "No text provided",
                "status": "error"
            }), 400
        
        # Analyze the entry
        analysis = analyze_entry(text)
        
        # Save to database
        entry = JournalEntry(
            text=text,
            sentiment=analysis['sentiment_analysis']['polarity'],
            emotions=analysis['sentiment_analysis'],
            themes={},  # Placeholder for future implementation
            user_id=current_user.id  # Associate entry with current user
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "analysis": analysis['analysis'],
            "sentiment": analysis['sentiment_analysis']
        })
    except Exception as e:
        print(f"Error processing entry: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/test_openai', methods=['GET'])
def test_openai():
    try:
        # Print environment variables for debugging
        print("API Key:", "Present" if os.getenv("AZURE_OPENAI_API_KEY") else "Missing")
        print("API Version:", os.getenv("AZURE_OPENAI_API_VERSION"))
        print("Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
        print("Deployment:", os.getenv("AZURE_OPENAI_DEPLOYMENT"))

        # Initialize Azure OpenAI client with proper error handling
        if not all([
            os.getenv("AZURE_OPENAI_API_KEY"),
            os.getenv("AZURE_OPENAI_API_VERSION"),
            os.getenv("AZURE_OPENAI_ENDPOINT"),
            os.getenv("AZURE_OPENAI_DEPLOYMENT")
        ]):
            raise ValueError("Missing required Azure OpenAI environment variables")

        # Initialize client with only the required parameters
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, can you hear me?"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        return jsonify({
            "status": "success",
            "message": "Azure OpenAI connection successful",
            "response": response.choices[0].message.content
        })
    except Exception as e:
        # Only print error if it's not the proxies error
        if "proxies" not in str(e):
            print(f"Detailed Error: {str(e)}")
            print(f"Error Type: {type(e)}")
        
        return jsonify({
            "status": "error",
            "message": "Azure OpenAI connection failed",
            "error": str(e),
            "error_type": str(type(e))
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({'status': 'success', 'redirect': url_for('dashboard')})
    
    return jsonify({'status': 'error', 'message': 'Invalid username or password'})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'message': 'Username already exists'})
    
    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': 'Email already registered'})
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html') 