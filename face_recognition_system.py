import face_recognition
import cv2
import numpy as np
import json
import base64
from PIL import Image
import io
import streamlit as st
import logging

class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.tolerance = 0.6
        
    def encode_face_from_image(self, image):
        """Extract face encoding from image"""
        try:
            # Convert PIL Image to RGB array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)
            
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) == 0:
                return None, "No face detected in the image"
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please ensure only one face is visible"
            
            face_encodings = face_recognition.face_encodings(image, face_locations)
            if len(face_encodings) == 0:
                return None, "Could not extract face features"
            
            return face_encodings[0].tolist(), "Face encoded successfully"
            
        except Exception as e:
            logging.error(f"Error encoding face: {e}")
            return None, f"Error processing face: {str(e)}"
    
    def load_known_faces(self, employees):
        """Load known faces from employee database"""
        self.known_face_encodings = []
        self.known_face_names = []
        
        for employee in employees:
            if employee.face_encoding:
                try:
                    encoding = json.loads(employee.face_encoding)
                    self.known_face_encodings.append(np.array(encoding))
                    self.known_face_names.append(employee.username)
                except Exception as e:
                    logging.error(f"Error loading face encoding for {employee.username}: {e}")
    
    def recognize_face(self, image):
        """Recognize face from image"""
        try:
            # Convert PIL Image to RGB array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)
            
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) == 0:
                return None, "No face detected"
            
            face_encodings = face_recognition.face_encodings(image, face_locations)
            if len(face_encodings) == 0:
                return None, "Could not extract face features"
            
            # Compare with known faces
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=self.tolerance
                )
                
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                
                if True in matches:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        confidence = 1 - face_distances[best_match_index]
                        return {
                            'username': self.known_face_names[best_match_index],
                            'confidence': confidence,
                            'face_location': face_locations[0]
                        }, "Face recognized successfully"
            
            return None, "Face not recognized"
            
        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return None, f"Error processing face: {str(e)}"
    
    def draw_face_rectangle(self, image, face_location, name, confidence):
        """Draw rectangle around recognized face"""
        top, right, bottom, left = face_location
        
        # Draw rectangle
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Add label
        label = f"{name} ({confidence:.2f})"
        cv2.rectangle(image, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
        cv2.putText(image, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return image

# Initialize face recognition system
face_recognition_system = FaceRecognitionSystem()