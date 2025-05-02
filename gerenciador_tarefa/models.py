from datetime import datetime, timedelta  # Importa classes para trabalhar com datas e intervalos de tempo
from flask_sqlalchemy import SQLAlchemy    # Importa a extensão para usar banco de dados com SQLAlchemy no Flask

db = SQLAlchemy()  # Inicializa o objeto do banco de dados, que será configurado depois no app principal

# Define a classe Tarefa como modelo do banco de dados
class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID único da tarefa (chave primária)
    nome = db.Column(db.String(100), nullable=False)  # Nome da tarefa, obrigatório
    descricao = db.Column(db.Text)  # Descrição da tarefa (campo de texto grande)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)  # Data de criação, valor padrão é o momento atual
    data_entrega = db.Column(db.DateTime, nullable=False)  # Data de entrega obrigatória
    data_conclusao = db.Column(db.DateTime)  # Data em que a tarefa foi concluída (opcional)
    concluida = db.Column(db.Boolean, default=False)  # Se a tarefa foi concluída ou não, padrão é False

    # Método para verificar o prazo da tarefa
    def verificar_prazo(self):
        hoje = datetime.utcnow()  # Obtém a data atual no formato UTC
        if self.concluida:
            return "concluída"  # Se a tarefa já está concluída
        elif self.data_entrega < hoje:
            return "atrasada"  # Se a data de entrega já passou
        elif (self.data_entrega - hoje) <= timedelta(days=3):
            return "proximo"  # Se faltam 2 dias ou menos para a entrega
        else:
            return "normal"  # Caso contrário, está dentro do prazo

    # Método que calcula os dias entre criação e entrega/conclusão
    def dias_para_entrega(self):
        if self.concluida:
            # Se concluída, retorna quantos dias levou para concluir
            return (self.data_conclusao - self.data_criacao).days
        elif self.data_entrega < datetime.utcnow():
            # Se já passou do prazo e não foi concluída, retorna dias desde a criação até agora
            return (datetime.utcnow() - self.data_criacao).days
        else:
            # Caso ainda esteja no prazo, retorna os dias restantes
            return (self.data_entrega - datetime.utcnow()).days

    # Método que retorna o status da entrega
    def status_entrega(self):
        if not self.concluida:
            return "pendente"  # Se ainda não foi concluída
        # Se foi concluída, verifica se foi no prazo ou atrasada
        return "no prazo" if self.data_conclusao <= self.data_entrega else "atrasada"
