from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta , date
from models import db, Tarefa, Garantia

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarefas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta_aqui'  # Substitua por uma chave segura em produção

db.init_app(app)

with app.app_context():
    db.create_all()

# Rota principal
@app.route('/')
def index():
    tarefas = Tarefa.query.filter_by(concluida=False).order_by(Tarefa.data_entrega).all()
    hoje = datetime.utcnow()

    for tarefa in tarefas:
        if hasattr(tarefa, 'verificar_prazo'):
            status = tarefa.verificar_prazo()
            if status == "atrasada":
                flash(f'Tarefa "{tarefa.nome}" está ATRASADA!', 'danger')
            elif status == "proximo":
                flash(f'Tarefa "{tarefa.nome}" está com prazo próximo (2 dias ou menos)', 'warning')

    return render_template('index.html', tarefas=tarefas, hoje=hoje)

# Adicionar tarefa
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
            if data_entrega.date() < datetime.utcnow().date():
                flash('A data de entrega não pode ser no passado!', 'danger')
                return redirect(url_for('adicionar_tarefa'))
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('adicionar_tarefa'))

        nova_tarefa = Tarefa(nome=nome, descricao=descricao, data_entrega=data_entrega)

        try:
            db.session.add(nova_tarefa)
            db.session.commit()
            flash('Tarefa adicionada com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception:
            db.session.rollback()
            flash('Erro ao adicionar tarefa.', 'danger')

    return render_template('adicionar_tarefa.html')

# Concluir tarefa
@app.route('/concluir_tarefa/<int:tarefa_id>')
def concluir_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    tarefa.concluida = True
    tarefa.data_conclusao = datetime.utcnow()

    try:
        db.session.commit()
        flash('Serviço marcado como concluído e movido para o histórico!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao concluir tarefa.', 'danger')

    return redirect(url_for('index'))

# Histórico
@app.route('/historico')
def historico():
    tarefas_concluidas = Tarefa.query.filter_by(concluida=True).order_by(Tarefa.data_conclusao.desc()).all()
    garantias_concluidas = Garantia.query.filter_by(concluida=True).order_by(Garantia.data_conclusao.desc()).all()

    historico = []

    for tarefa in tarefas_concluidas:
        historico.append({
            'tipo': 'servico',
            'id': tarefa.id,
            'nome': tarefa.nome,
            'data_criacao': tarefa.data_criacao,
            'data_entrega': tarefa.data_entrega,
            'data_conclusao': tarefa.data_conclusao,
            'status': tarefa.status_entrega() if hasattr(tarefa, 'status_entrega') else '',
            'dias_realizacao': (tarefa.data_conclusao - tarefa.data_criacao).days
        })

    for garantia in garantias_concluidas:
        status = 'concluida' if garantia.data_entrega >= garantia.data_conclusao else 'expirada'
        historico.append({
            'tipo': 'garantia',
            'id': garantia.id,
            'nome': garantia.nome,
            'data_criacao': garantia.data_inicio,
            'data_entrega': garantia.data_entrega,
            'data_conclusao': garantia.data_conclusao,
            'status': status,
            'dias_realizacao': (garantia.data_conclusao - garantia.data_inicio).days
        })

    historico.sort(key=lambda x: x['data_conclusao'], reverse=True)
    return render_template('historico.html', historico=historico)

# Excluir tarefa
@app.route('/excluir_tarefa/<int:id>', methods=['POST'])
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)

    try:
        db.session.delete(tarefa)
        db.session.commit()
        flash('Tarefa excluída com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir tarefa.', 'danger')

    return redirect(url_for('historico'))

# Editar tarefa
@app.route('/editar_tarefa/<int:tarefa_id>', methods=['GET', 'POST'])
def editar_tarefa(tarefa_id):
    tarefa = Tarefa.query.get_or_404(tarefa_id)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_entrega_str = request.form.get('data_entrega', '')

        if not nome:
            flash('O nome da tarefa é obrigatório.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))

        try:
            nova_data = datetime.strptime(data_entrega_str, '%Y-%m-%d')
            if nova_data.date() < datetime.utcnow().date():
                flash('A data de entrega não pode ser no passado!', 'danger')
                return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))
            tarefa.data_entrega = nova_data
        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('editar_tarefa', tarefa_id=tarefa.id))

        tarefa.nome = nome
        tarefa.descricao = descricao

        try:
            db.session.commit()
            flash('Tarefa atualizada com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar tarefa.', 'danger')

    return render_template('editar_tarefa.html', tarefa=tarefa)

# Lista de garantias
@app.route('/garantias')
def lista_garantias():
    garantias = Garantia.query.filter_by(concluida=False).order_by(Garantia.data_entrega).all()
    hoje = date.today()
    expired, nearing = [], []

    for garantia in garantias:
        if garantia.data_entrega < hoje:
            garantia.status = 'expirada'
            expired.append(garantia.nome)
        elif (garantia.data_entrega - hoje) <= timedelta(days=30):
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
        data_entrega_str = request.form.get('data_entrega', '')

        if not nome:
            flash('O nome da garantia é obrigatório.', 'danger')
            return redirect(url_for('adicionar_garantia'))

        try:
            data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d')

            if data_entrega.date() < date.today():
                flash('A data de entrega deve ser após a data inicial.', 'danger')
                return redirect(url_for('adicionar_garantia'))

        except ValueError:
            flash('Formato de data inválido. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('adicionar_garantia'))

        nova_garantia = Garantia(
            nome=nome,
            descricao=descricao,
            data_entrega=data_entrega
        )

        try:
            db.session.add(nova_garantia)
            db.session.commit()
            flash('Garantia adicionada com sucesso!', 'success')
            return redirect(url_for('lista_garantias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar garantia: {str(e)}', 'danger')
            print(f"Erro ao adicionar garantia: {str(e)}")

    return render_template("adicionar_garantia.html", date=date)


# Inicializador
if __name__ == '__main__':
    app.run(debug=True)
