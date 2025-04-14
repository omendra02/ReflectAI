# ReflectAI - Your Personal Journal Companion

ReflectAI is an AI-powered journaling application that helps users track their emotional well-being and personal growth through intelligent sentiment analysis and personalized insights.

## Features

- **Smart Journaling**: Write your daily thoughts and receive AI-powered analysis
- **Sentiment Analysis**: Get detailed emotional insights from your entries
- **User Authentication**: Secure login and registration system
- **Modern UI**: Clean, responsive interface built with Tailwind CSS
- **Data Privacy**: Your journal entries are securely stored and private

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **AI/ML**: Azure OpenAI API, TextBlob for sentiment analysis
- **Authentication**: Flask-Login

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ReflectAI.git
cd ReflectAI
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_API_VERSION=your_api_version
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
ReflectAI/
├── app/
│   ├── static/
│   │   └── images/
│   │   
│   ├── templates/
│   │   ├── dashboard.html
│   │   ├── index.html
│   │   ├── login.html
│   │   └── signup.html
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
├── venv/
├── .env
├── .gitignore
├── init_db.py
├── requirements.txt
├── README.md
└── run.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and Azure OpenAI
- UI components powered by Tailwind CSS
- Icons from Heroicons 