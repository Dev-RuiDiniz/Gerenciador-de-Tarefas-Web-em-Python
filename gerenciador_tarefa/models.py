from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_entrega = db.Column(db.DateTime, nullable=False)
    data_conclusao = db.Column(db.DateTime)
    concluida = db.Column(db.Boolean, default=False)
    
    def verificar_prazo(self):
        hoje = datetime.utcnow()
        if self.concluida:
            return "concluída"
        elif self.data_entrega < hoje:
            return "atrasada"
        elif (self.data_entrega - hoje) <= timedelta(days=2):
            return "proximo"
        else:
            return "normal"
    
    def dias_para_entrega(self):
        if self.concluida:
            return (self.data_conclusao - self.data_criacao).days
        elif self.data_entrega < datetime.utcnow():
            return (datetime.utcnow() - self.data_criacao).days
        else:
            return (self.data_entrega - datetime.utcnow()).days
    
    def status_entrega(self):
        if not self.concluida:
            return "pendente"
        return "no prazo" if self.data_conclusao <= self.data_entrega else "atrasada"