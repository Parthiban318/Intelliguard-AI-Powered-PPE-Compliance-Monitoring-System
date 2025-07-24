from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import torch
import logging
from config import config

class PPEDetector:
    def __init__(self, model_path=None):
        """Initialize PPE detector"""
        self.model_path = model_path or "yolov8n.pt"  # Default to pretrained YOLOv8
        self.model = None
        self.class_names = config.PPE_CLASSES
        self.violation_classes = config.VIOLATION_CLASSES
        self.load_model()
        
    def load_model(self):
        """Load YOLO model"""
        try:
            self.model = YOLO(self.model_path)
            logging.info(f"Model loaded successfully from {self.model_path}")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            # Load default model as fallback
            self.model = YOLO("yolov8n.pt")
    
    def detect_ppe(self, image, confidence_threshold=0.5):
        """Detect PPE in image"""
        try:
            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)
            
            # Run inference
            results = self.model(image, conf=confidence_threshold)
            
            detections = []
            violations = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Get class name (use index if available, otherwise use generic names)
                        if class_id < len(self.class_names):
                            class_name = self.class_names[class_id]
                        else:
                            class_name = f"object_{class_id}"
                        
                        detection = {
                            'class_name': class_name,
                            'confidence': float(confidence),
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'width': float(x2 - x1),
                            'height': float(y2 - y1)
                        }
                        
                        detections.append(detection)
                        
                        # Check if it's a violation
                        if class_name in self.violation_classes:
                            violation = {
                                'violation_type': class_name,
                                'severity': self.get_violation_severity(class_name),
                                'confidence': float(confidence),
                                'bbox_x': float(x1),
                                'bbox_y': float(y1),
                                'bbox_width': float(x2 - x1),
                                'bbox_height': float(y2 - y1)
                            }
                            violations.append(violation)
            
            # Determine compliance status
            compliance_status = self.get_compliance_status(detections, violations)
            
            return {
                'detections': detections,
                'violations': violations,
                'total_detections': len(detections),
                'violation_count': len(violations),
                'compliance_status': compliance_status,
                'average_confidence': np.mean([d['confidence'] for d in detections]) if detections else 0.0
            }
            
        except Exception as e:
            logging.error(f"Error during PPE detection: {e}")
            return {
                'detections': [],
                'violations': [],
                'total_detections': 0,
                'violation_count': 0,
                'compliance_status': 'ERROR',
                'average_confidence': 0.0
            }
    
    def get_violation_severity(self, violation_type):
        """Get severity level for violation type"""
        severity_map = {
            'no_helmet': 'CRITICAL',
            'no_mask': 'HIGH',
            'no_goggles': 'MEDIUM',
            'no_glove': 'MEDIUM',
            'no_shoes': 'MEDIUM',
            'no-suit': 'HIGH'
        }
        return severity_map.get(violation_type, 'MEDIUM')
    
    def get_compliance_status(self, detections, violations):
        """Determine overall compliance status"""
        if len(violations) == 0:
            return 'COMPLIANT'
        elif len(violations) >= len(detections) * 0.5:  # More than 50% violations
            return 'VIOLATION'
        else:
            return 'PARTIAL'
    
    def draw_detections(self, image, detections):
        """Draw detection boxes on image"""
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        image_copy = image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Choose color based on detection type
            if class_name in self.violation_classes:
                color = (255, 0, 0)  # Red for violations
            else:
                color = (0, 255, 0)  # Green for compliance
            
            # Draw rectangle
            cv2.rectangle(image_copy, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # Add label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            cv2.rectangle(
                image_copy,
                (int(x1), int(y1) - label_size[1] - 10),
                (int(x1) + label_size[0], int(y1)),
                color,
                -1
            )
            
            cv2.putText(
                image_copy,
                label,
                (int(x1), int(y1) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        return image_copy
    
    def train_custom_model(self, data_yaml_path, epochs=100, imgsz=640):
        """Train custom PPE detection model"""
        try:
            # Initialize model for training
            model = YOLO("yolov8n.pt")
            
            # Train the model
            results = model.train(
                data=data_yaml_path,
                epochs=epochs,
                imgsz=imgsz,
                save=True,
                project="ppe_training",
                name="ppe_detector",
                exist_ok=True
            )
            
            return results
        except Exception as e:
            logging.error(f"Error training model: {e}")
            return None

# Initialize PPE detector
ppe_detector = PPEDetector()