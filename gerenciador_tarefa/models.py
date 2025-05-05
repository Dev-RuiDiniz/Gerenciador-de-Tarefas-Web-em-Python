from datetime import datetime, timedelta  # Importa funções para lidar com datas e horários
from flask_sqlalchemy import SQLAlchemy   # Importa o ORM do Flask para manipular banco de dados relacional

db = SQLAlchemy()  # Cria uma instância do SQLAlchemy para integração com o Flask

# Define a classe "Tarefa" como um modelo do banco de dados
class Tarefa(db.Model):
    # Coluna ID (chave primária, valor inteiro único e auto incrementável)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Nome da tarefa, obrigatório (não pode ser nulo), com limite de 100 caracteres
    nome = db.Column(db.String(100), nullable=False)

    # Descrição da tarefa (campo de texto livre)
    descricao = db.Column(db.Text)

    # Data de criação da tarefa, preenchida automaticamente com o horário atual (UTC)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Data limite para entrega da tarefa (obrigatória)
    data_entrega = db.Column(db.DateTime, nullable=False)

    # Data em que a tarefa foi concluída (opcional)
    data_conclusao = db.Column(db.DateTime)

    # Indica se a tarefa foi concluída ou não (booleano, padrão é False)
    concluida = db.Column(db.Boolean, default=False)
    
    # Método para verificar a situação do prazo da tarefa
    def verificar_prazo(self):
        hoje = datetime.utcnow()  # Obtém a data e hora atual
        if self.concluida:
            return "concluída"  # Se já foi concluída
        elif self.data_entrega < hoje:
            return "atrasada"  # Se a data de entrega já passou
        elif (self.data_entrega - hoje) <= timedelta(days=3):
            return "proximo"  # Se faltam 3 dias ou menos
        else:
            return "normal"  # Caso contrário, está dentro do prazo

    # Método para calcular quantos dias faltam para a entrega (ou quanto tempo levou para concluir)
    def dias_para_entrega(self):
        if self.concluida:
            return (self.data_conclusao - self.data_criacao).days  # Diferença entre criação e conclusão
        elif self.data_entrega < datetime.utcnow():
            return (datetime.utcnow() - self.data_criacao).days  # Tarefa em atraso
        else:
            return (self.data_entrega - datetime.utcnow()).days  # Dias restantes até a entrega

    # Método para retornar o status da entrega com base na conclusão e prazo
    def status_entrega(self):
        if not self.concluida:
            return "pendente"  # Ainda não foi concluída
        return "no prazo" if self.data_conclusao <= self.data_entrega else "atrasada"  # Verifica se foi concluída em tempo

class Garantia(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)  # antes era data_inicio
    data_entrega = db.Column(db.DateTime, nullable=False)           # antes era data_fim
    data_conclusao = db.Column(db.DateTime)
    concluida = db.Column(db.Boolean, default=False)

    def verificar_prazo(self):
        hoje = datetime.utcnow()
        if self.concluida:
            return "concluída"
        elif self.data_entrega < hoje:
            return "atrasada"
        elif (self.data_entrega - hoje) <= timedelta(days=3):
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