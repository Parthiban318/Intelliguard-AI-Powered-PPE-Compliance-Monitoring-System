from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms import OpenAI
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
import pandas as pd
import logging
from config import config

class PPEChatbot:
    def __init__(self):
        """Initialize PPE Compliance Chatbot"""
        self.db = None
        self.agent = None
        self.setup_database()
        self.setup_agent()
    
    def setup_database(self):
        """Setup database connection for chatbot"""
        try:
            self.db = SQLDatabase.from_uri(config.DATABASE_URL)
            logging.info("Database connection established for chatbot")
        except Exception as e:
            logging.error(f"Error setting up database for chatbot: {e}")
    
    def setup_agent(self):
        """Setup LangChain SQL agent"""
        try:
            if not config.OPENAI_API_KEY:
                logging.error("OpenAI API key not found")
                return
            
            llm = OpenAI(
                temperature=0,
                openai_api_key=config.OPENAI_API_KEY
            )
            
            toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
            
            self.agent = create_sql_agent(
                llm=llm,
                toolkit=toolkit,
                verbose=True,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
            )
            
            logging.info("Chatbot agent initialized successfully")
        except Exception as e:
            logging.error(f"Error setting up chatbot agent: {e}")
    
    def get_response(self, question):
        """Get response from chatbot"""
        try:
            if not self.agent:
                return "Chatbot is not properly initialized. Please check your OpenAI API key."
            
            # Add context to the question
            context = """
            You are an AI assistant for PPE (Personal Protective Equipment) compliance monitoring.
            
            Database schema:
            - employees: stores employee information (id, username, first_name, last_name, email, department, role)
            - ppe_detections: stores detection records (id, employee_id, detection_timestamp, total_detections, violation_count, compliance_status)
            - violations: stores violation details (id, detection_id, employee_id, violation_type, severity, confidence, timestamp, resolved)
            - audit_logs: stores user activity logs
            
            PPE violation types: no_helmet, no_mask, no_goggles, no_glove, no_shoes, no-suit
            Severity levels: LOW, MEDIUM, HIGH, CRITICAL
            Compliance status: COMPLIANT, VIOLATION, PARTIAL
            
            When answering questions:
            1. Be specific and provide relevant data
            2. Include statistics when appropriate
            3. Mention safety recommendations for violations
            4. Format responses clearly
            
            Question: """
            
            full_question = context + question
            response = self.agent.run(full_question)
            
            return response
            
        except Exception as e:
            logging.error(f"Error getting chatbot response: {e}")
            return f"I apologize, but I encountered an error processing your question: {str(e)}. Please try rephrasing your question or contact support."
    
    def get_quick_stats(self):
        """Get quick statistics for dashboard"""
        try:
            if not self.db:
                return "Database not available"
            
            query = """
            SELECT 
                COUNT(DISTINCT e.id) as total_employees,
                COUNT(pd.id) as total_detections,
                COUNT(v.id) as total_violations,
                ROUND(AVG(CASE WHEN pd.compliance_status = 'COMPLIANT' THEN 1.0 ELSE 0.0 END) * 100, 2) as compliance_rate
            FROM employees e
            LEFT JOIN ppe_detections pd ON e.id = pd.employee_id
            LEFT JOIN violations v ON pd.id = v.detection_id
            WHERE pd.detection_timestamp >= CURRENT_DATE - INTERVAL '30 days' OR pd.detection_timestamp IS NULL;
            """
            
            result = self.db.run(query)
            return f"📊 **Quick Stats (Last 30 Days):**\n{result}"
            
        except Exception as e:
            logging.error(f"Error getting quick stats: {e}")
            return "Unable to retrieve statistics at the moment."
    
    def suggest_questions(self):
        """Suggest common questions users might ask"""
        suggestions = [
            "How many PPE violations were detected today?",
            "What is the current compliance rate?",
            "Which department has the most violations?",
            "What are the most common types of violations?",
            "Show me recent helmet violations",
            "Which employees have the most violations?",
            "What is the trend of violations over the past month?",
            "How many resolved violations do we have?",
            "Which violations are marked as critical?"
        ]
        return suggestions

# Initialize chatbot
chatbot = PPEChatbot()