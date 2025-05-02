# Importa as bibliotecas necessárias
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from models import db, Tarefa  # Importa a configuração do banco de dados e o modelo Tarefa

# Inicializa o aplicativo Flask
app = Flask(__name__)
# Configuração da URI do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarefas.db'
# Desativa rastreamento de modificações para economizar recursos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Define uma chave secreta para sessões seguras e mensagens flash
app.secret_key = 'sua_chave_secreta_aqui'

# Inicializa a extensão SQLAlchemy com o app
db.init_app(app)

# Cria as tabelas do banco de dados se ainda não existirem
with app.app_context():
    db.create_all()

# Rota principal que exibe as tarefas pendentes
@app.route('/')
def index():
    # Busca tarefas não concluídas ordenadas pela data de entrega
    tarefas = Tarefa.query.filter_by(concluida=False).order_by(Tarefa.data_entrega).all()
    hoje = datetime.utcnow()
    
    # Verifica o status de prazo de cada tarefa e exibe alertas se necessário
    for tarefa in tarefas:
        if tarefa.verificar_prazo() == "atrasada":
            flash(f'Tarefa "{tarefa.nome}" está ATRASADA!', 'danger')
        elif tarefa.verificar_prazo() == "proximo":
            flash(f'Tarefa "{tarefa.nome}" está com prazo próximo (2 dias ou menos)', 'warning')
    
    return render_template('index.html', tarefas=tarefas, hoje=hoje)

# Rota para adicionar nova tarefa
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_tarefa():
    if request.method == 'POST':
        # Obtém os dados do formulário
        nome = request.form['nome']
        descricao = request.form['descricao']
        data_entrega_str = request.form['data_entrega']
        
        # Tenta converter a data recebida em string para objeto datetime
        try:
            data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('adicionar_tarefa'))
        
        # Verifica se a data de entrega está no futuro
        if data_entrega < datetime.utcnow():
            flash('A data de entrega não pode ser no passado!', 'danger')
            return redirect(url_for('adicionar_tarefa'))
        
        # Cria a nova tarefa e salva no banco
        nova_tarefa = Tarefa(
            nome=nome,
            descricao=descricao,
            data_entrega=data_entrega
        )
        
        db.session.add(nova_tarefa)
        db.session.commit()
        flash('Tarefa adicionada com sucesso!', 'success')
        return redirect(url_for('index'))
    
    return render_template('adicionar_tarefa.html')

# Rota para marcar tarefa como concluída
@app.route('/concluir/<int:tarefa_id>')
def concluir_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    tarefa.concluida = True
    tarefa.data_conclusao = datetime.utcnow()
    db.session.commit()
    flash('Tarefa marcada como concluída!', 'success')
    return redirect(url_for('index'))

# Rota para exibir o histórico de tarefas concluídas
@app.route('/historico')
def historico():
    tarefas_concluidas = Tarefa.query.filter_by(concluida=True).order_by(Tarefa.data_conclusao.desc()).all()
    historico = []
    
    # Formata os dados para serem exibidos no histórico
    for tarefa in tarefas_concluidas:
        historico.append({
            'id': tarefa.id,
            'nome': tarefa.nome,
            'data_criacao': tarefa.data_criacao,
            'data_entrega': tarefa.data_entrega,
            'data_conclusao': tarefa.data_conclusao,
            'status': tarefa.status_entrega(),  # Verifica se a entrega foi em dia ou atrasada
            'dias_realizacao': (tarefa.data_conclusao - tarefa.data_criacao).days
        })
    
    return render_template('historico.html', historico=historico)

# Rota para excluir uma tarefa do histórico
@app.route('/excluir_tarefa/<int:id>', methods=['POST'])
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    db.session.delete(tarefa)
    db.session.commit()
    flash('Tarefa excluída com sucesso.', 'success')
    return redirect(url_for('historico'))

# Rota para editar uma tarefa existente
@app.route('/editar/<int:tarefa_id>', methods=['GET', 'POST'])
def editar_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)

    if request.method == 'POST':
        # Atualiza os dados da tarefa
        tarefa.nome = request.form['nome']
        tarefa.descricao = request.form['descricao']
        
        try:
            tarefa.data_entrega = datetime.strptime(request.form['data_entrega'], '%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))

        db.session.commit()
        flash('Tarefa atualizada com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('editar_tarefa.html', tarefa=tarefa)

# Executa a aplicação se este arquivo for executado diretamente
if __name__ == '__main__':
    app.run(debug=True)
