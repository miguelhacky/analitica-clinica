import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import json
import os
import joblib


class ClinicalPredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_names = ['edad', 'IMC', 'glucosa', 'colesterol',
                              'presion_sistolica', 'frecuencia_cardiaca', 'fumador_Sí']
        self.metrics = {}
        self.model_path = None

    def prepare_data(self, pacientes_qs):
        data = []
        for p in pacientes_qs:
            data.append({
                'edad': p.edad,
                'IMC': p.IMC or 0,
                'glucosa': p.glucosa,
                'colesterol': p.colesterol,
                'presion_sistolica': p.presion_sistolica,
                'frecuencia_cardiaca': p.frecuencia_cardiaca,
                'fumador_Sí': 1 if p.fumador == 'Sí' else 0,
                'riesgo': p.riesgo_enfermedad,
            })
        return pd.DataFrame(data)

    def train(self, pacientes_qs, model_type='random_forest'):
        df = self.prepare_data(pacientes_qs)

        if len(df) < 10:
            return False

        le = LabelEncoder()
        df['riesgo_encoded'] = le.fit_transform(df['riesgo'])
        self.label_encoders['riesgo'] = le

        X = df[self.feature_names]
        y = df['riesgo_encoded']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42
            )
        elif model_type == 'logistic_regression':
            self.model = LogisticRegression(max_iter=1000, random_state=42)
        elif model_type == 'decision_tree':
            self.model = DecisionTreeClassifier(max_depth=10, random_state=42)
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)

        self.metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
            'model_type': model_type,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
        }

        cm = confusion_matrix(y_test, y_pred)
        self.metrics['confusion_matrix'] = cm.tolist()
        self.metrics['classes'] = le.classes_.tolist()

        return True

    def predict(self, paciente):
        if self.model is None:
            return {'riesgo': 'Desconocido', 'probabilidad': 0}

        data = pd.DataFrame([{
            'edad': paciente.edad,
            'IMC': paciente.IMC or 0,
            'glucosa': paciente.glucosa,
            'colesterol': paciente.colesterol,
            'presion_sistolica': paciente.presion_sistolica,
            'frecuencia_cardiaca': paciente.frecuencia_cardiaca,
            'fumador_Sí': 1 if paciente.fumador == 'Sí' else 0,
        }])

        data = data[self.feature_names]

        proba = self.model.predict_proba(data)[0]
        pred = self.model.predict(data)[0]

        le = self.label_encoders.get('riesgo')
        riesgo_label = le.inverse_transform([pred])[0] if le else str(pred)
        max_prob = float(max(proba))

        return {
            'riesgo': riesgo_label,
            'probabilidad': round(max_prob, 4),
            'probabilidades': {
                str(le.inverse_transform([i])[0] if le else i): float(p)
                for i, p in enumerate(proba)
            }
        }

    def save_model(self, path):
        joblib.dump({
            'model': self.model,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'metrics': self.metrics,
        }, path)
        self.model_path = path

    def load_model(self, path):
        data = joblib.load(path)
        self.model = data['model']
        self.label_encoders = data['label_encoders']
        self.feature_names = data['feature_names']
        self.metrics = data['metrics']
        self.model_path = path


predictor = ClinicalPredictor()
