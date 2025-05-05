from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
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
        
        try:
            db.session.add(nova_tarefa)
            db.session.commit()
            flash('Tarefa adicionada com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar tarefa.', 'danger')
            return redirect(url_for('adicionar_tarefa'))
    
    return render_template('adicionar_tarefa.html')

@app.route('/concluir_tarefa/<int:tarefa_id>')
def concluir_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    tarefa.concluida = True
    tarefa.data_conclusao = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Serviço marcado como concluído e movido para o histórico!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao concluir tarefa.', 'danger')
    
    return redirect(url_for('index'))

@app.route('/historico')
def historico():
    # Histórico de tarefas (serviços)
    tarefas_concluidas = Tarefa.query.filter_by(concluida=True).order_by(Tarefa.data_conclusao.desc()).all()
    
    # Histórico de garantias
    garantias_concluidas = Garantia.query.filter_by(concluida=True).order_by(Garantia.data_conclusao.desc()).all()
    
    historico = []
    
    # Processar tarefas
    for tarefa in tarefas_concluidas:
        historico.append({
            'tipo': 'servico',
            'id': tarefa.id,
            'nome': tarefa.nome,
            'data_criacao': tarefa.data_criacao,
            'data_entrega': tarefa.data_entrega,
            'data_conclusao': tarefa.data_conclusao,
            'status': tarefa.status_entrega(),
            'dias_realizacao': (tarefa.data_conclusao - tarefa.data_criacao).days
        })
    
    # Processar garantias
    for garantia in garantias_concluidas:
        status = 'concluida'
        if garantia.data_fim < garantia.data_conclusao:
            status = 'expirada'
        
        historico.append({
            'tipo': 'garantia',
            'id': garantia.id,
            'nome': garantia.nome,
            'data_criacao': garantia.data_inicio,
            'data_entrega': garantia.data_fim,
            'data_conclusao': garantia.data_conclusao,
            'status': status,
            'dias_realizacao': (garantia.data_conclusao - garantia.data_inicio).days
        })
    
    # Ordenar por data de conclusão (mais recente primeiro)
    historico.sort(key=lambda x: x['data_conclusao'], reverse=True)
    
    return render_template('historico.html', historico=historico)

@app.route('/excluir_tarefa/<int:id>', methods=['POST'])
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    
    try:
        db.session.delete(tarefa)
        db.session.commit()
        flash('Tarefa excluída com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir tarefa.', 'danger')
    
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
            nova_data = datetime.strptime(request.form.get('data_entrega', ''), '%Y-%m-%d')
            if nova_data < datetime.utcnow():
                flash('A data de entrega não pode ser no passado!', 'danger')
                return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))
            tarefa.data_entrega = nova_data
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))

        try:
            db.session.commit()
            flash('Tarefa atualizada com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar tarefa.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))

    return render_template('editar_tarefa.html', tarefa=tarefa)

@app.route('/garantias')
def lista_garantias():
    garantias = Garantia.query.filter_by(concluida=False).order_by(Garantia.data_fim).all()
    hoje = datetime.utcnow()
    expired = []
    nearing = []
    
    for garantia in garantias:
        if garantia.data_fim < hoje:
            garantia.status = 'expirada'
            expired.append(garantia.nome)
        elif (garantia.data_fim - hoje) <= timedelta(days=30):
            garantia.status = 'proximo'
            nearing.append(garantia.nome)
        else:
            garantia.status = 'ativa'
    
    if expired:
        flash(f'Garantias expiradas: {", ".join(expired)}', 'danger')
    if nearing:
        flash(f'Garantias próximas do vencimento: {", ".join(nearing)}', 'warning')
    
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
            
            if data_fim < data_inicio:
                flash('A data final deve ser após a data inicial.', 'danger')
                return redirect(url_for('adicionar_garantia'))
            
            if data_inicio < datetime.utcnow().date():
                flash('A data inicial não pode ser no passado.', 'danger')
                return redirect(url_for('adicionar_garantia'))
                
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('adicionar_garantia'))

        nova_garantia = Garantia(
            nome=nome, 
            descricao=descricao, 
            data_inicio=data_inicio, 
            data_fim=data_fim
        )
        
        try:
            db.session.add(nova_garantia)
            db.session.commit()
            flash('Garantia adicionada com sucesso!', 'success')
            return redirect(url_for('lista_garantias'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar garantia.', 'danger')
            return redirect(url_for('adicionar_garantia'))
    
    return render_template('adicionar_garantia.html')

@app.route('/concluir_garantia/<int:garantia_id>')
def concluir_garantia(garantia_id):
    garantia = Garantia.query.get_or_404(garantia_id)
    garantia.concluida = True
    garantia.data_conclusao = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Garantia marcada como concluída!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao concluir garantia.', 'danger')
    
    return redirect(url_for('lista_garantias'))

@app.route('/editar_garantia/<int:garantia_id>', methods=['GET', 'POST'])
def editar_garantia(garantia_id):
    garantia = Garantia.query.get_or_404(garantia_id)

    if request.method == 'POST':
        garantia.nome = request.form.get('nome', '').strip()
        garantia.descricao = request.form.get('descricao', '').strip()
        
        if not garantia.nome:
            flash('O nome da garantia é obrigatório.', 'danger')
            return redirect(url_for('editar_garantia', garantia_id=garantia.id))
        
        try:
            data_inicio = datetime.strptime(request.form.get('data_inicio', ''), '%Y-%m-%d')
            data_fim = datetime.strptime(request.form.get('data_fim', ''), '%Y-%m-%d')
            
            if data_fim < data_inicio:
                flash('A data final deve ser após a data inicial.', 'danger')
                return redirect(url_for('editar_garantia', garantia_id=garantia.id))
            
            garantia.data_inicio = data_inicio
            garantia.data_fim = data_fim
            
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('editar_garantia', garantia_id=garantia.id))

        try:
            db.session.commit()
            flash('Garantia atualizada com sucesso!', 'success')
            return redirect(url_for('lista_garantias'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar garantia.', 'danger')
            return redirect(url_for('editar_garantia', garantia_id=garantia.id))

    return render_template('editar_garantia.html', garantia=garantia)

@app.route('/excluir_garantia/<int:id>', methods=['POST'])
def excluir_garantia(id):
    garantia = Garantia.query.get_or_404(id)
    
    try:
        db.session.delete(garantia)
        db.session.commit()
        flash('Garantia excluída com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir garantia.', 'danger')
    
    return redirect(url_for('historico'))

if __name__ == '__main__':
    app.run(debug=True)