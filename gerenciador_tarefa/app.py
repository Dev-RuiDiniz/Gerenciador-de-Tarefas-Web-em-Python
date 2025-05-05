from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import db, Tarefa, Garantia

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarefas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta_aqui'  # Substitua por uma chave segura em produção

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    tarefas = Tarefa.query.filter_by(concluida=False).order_by(Tarefa.data_entrega).all()
    hoje = datetime.utcnow()
    
    for tarefa in tarefas:
        status = tarefa.verificar_prazo()
        if status == "atrasada":
            flash(f'Tarefa "{tarefa.nome}" está ATRASADA!', 'danger')
        elif status == "proximo":
            flash(f'Tarefa "{tarefa.nome}" está com prazo próximo (2 dias ou menos)', 'warning')
    
    return render_template('index.html', tarefas=tarefas, hoje=hoje)

@app.route('/adicionar_tarefa', methods=['GET', 'POST'])
def adicionar_tarefa():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_entrega_str = request.form.get('data_entrega', '')
        
        if not nome:
            flash('O nome da tarefa é obrigatório.', 'danger')
            return redirect(url_for('adicionar_tarefa'))
        
        try:
            data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('adicionar_tarefa'))
        
        if data_entrega < datetime.utcnow():
            flash('A data de entrega não pode ser no passado!', 'danger')
            return redirect(url_for('adicionar_tarefa'))
        
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

@app.route('/concluir/<int:tarefa_id>')
def concluir_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    tarefa.concluida = True
    tarefa.data_conclusao = datetime.utcnow()
    db.session.commit()
    flash('Tarefa marcada como concluída!', 'success')
    return redirect(url_for('index'))

@app.route('/historico')
def historico():
    tarefas_concluidas = Tarefa.query.filter_by(concluida=True).order_by(Tarefa.data_conclusao.desc()).all()
    historico = []
    
    for tarefa in tarefas_concluidas:
        historico.append({
            'id': tarefa.id,
            'nome': tarefa.nome,
            'data_criacao': tarefa.data_criacao,
            'data_entrega': tarefa.data_entrega,
            'data_conclusao': tarefa.data_conclusao,
            'status': tarefa.status_entrega(),
            'dias_realizacao': (tarefa.data_conclusao - tarefa.data_criacao).days
        })
    
    return render_template('historico.html', historico=historico)

@app.route('/excluir_tarefa/<int:id>', methods=['POST'])
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    db.session.delete(tarefa)
    db.session.commit()
    flash('Tarefa excluída com sucesso.', 'success')
    return redirect(url_for('historico'))

@app.route('/editar_tarefa/<int:tarefa_id>', methods=['GET', 'POST'])
def editar_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)

    if request.method == 'POST':
        tarefa.nome = request.form.get('nome', '').strip()
        tarefa.descricao = request.form.get('descricao', '').strip()
        
        if not tarefa.nome:
            flash('O nome da tarefa é obrigatório.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))
        
        try:
            tarefa.data_entrega = datetime.strptime(request.form.get('data_entrega', ''), '%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))

        db.session.commit()
        flash('Tarefa atualizada com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('editar_tarefa.html', tarefa=tarefa)

@app.route('/garantias')
def lista_garantias():
    garantias = Garantia.query.order_by(Garantia.data_fim).all()
    hoje = datetime.utcnow()
    
    for garantia in garantias:
        if garantia.data_fim < hoje:
            garantia.status = 'expirada'
        elif (garantia.data_fim - hoje) <= timedelta(days=30):
            garantia.status = 'proximo'
        else:
            garantia.status = 'ativa'
    
    return render_template('garantias.html', garantias=garantias)

@app.route('/adicionar_garantia', methods=['GET', 'POST'])
def adicionar_garantia():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_inicio_str = request.form.get('data_inicio', '')
        data_fim_str = request.form.get('data_fim', '')
        
        if not nome:
            flash('O nome da garantia é obrigatório.', 'danger')
            return redirect(url_for('adicionar_garantia'))
        
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('adicionar_garantia'))

        if data_fim < data_inicio:
            flash('A data final deve ser após a data inicial.', 'danger')
            return redirect(url_for('adicionar_garantia'))

        nova_garantia = Garantia(
            nome=nome, 
            descricao=descricao, 
            data_inicio=data_inicio, 
            data_fim=data_fim
        )
        
        db.session.add(nova_garantia)
        db.session.commit()
        flash('Garantia adicionada com sucesso!', 'success')
        return redirect(url_for('lista_garantias'))
    
    return render_template('adicionar_garantia.html')

if __name__ == '__main__':
    app.run(debug=True)