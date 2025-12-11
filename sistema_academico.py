#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Acadêmico (arquivo único, orientação a objetos)
- SQLite local: gestor_academico.db
- CRUD Cursos / Turmas / Alunos
- Matrículas com validação completa
- Registro de notas e frequência
- Relatórios e listagens
"""

import sqlite3
import json
from dataclasses import dataclass, field
from typing import List, Optional

DB_NAME = "gestor_academico.db"

# ============================
# DATABASE
# ============================
def conectar():
    return sqlite3.connect(DB_NAME)

def inicializar():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cursos (
            codigo TEXT PRIMARY KEY,
            nome TEXT,
            prerequisitos TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS turmas (
            codigo TEXT PRIMARY KEY,
            curso_codigo TEXT,
            professor TEXT,
            horario TEXT,
            limite_vagas INTEGER,
            vagas_ocupadas INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            matricula TEXT PRIMARY KEY,
            nome TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS matriculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_matricula TEXT,
            turma_codigo TEXT,
            nota REAL,
            frequencia REAL
        )
    """)

    con.commit()
    con.close()


# ============================
# MODELOS
# ============================
class EntidadeBase:
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

@dataclass
class Curso(EntidadeBase):
    codigo: str
    nome: str
    prerequisitos: List[str] = field(default_factory=list)

@dataclass
class Turma(EntidadeBase):
    codigo: str
    curso_codigo: str
    professor: str
    horario: str       # formato esperado: dia-ini-fim, ex: seg-8-10
    limite_vagas: int
    vagas_ocupadas: int = 0

@dataclass
class Aluno(EntidadeBase):
    matricula: str
    nome: str

@dataclass
class Matricula(EntidadeBase):
    aluno_matricula: str
    turma_codigo: str
    nota: Optional[float] = None
    frequencia: Optional[float] = None


# ============================
# SERVIÇOS / LÓGICA
# ============================
# ----- consultas básicas -----
def curso_por_codigo(codigo: str) -> Optional[Curso]:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT codigo, nome, prerequisitos FROM cursos WHERE codigo=?", (codigo,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    prereq = json.loads(row[2]) if row[2] else []
    return Curso(row[0], row[1], prereq)

def turma_por_codigo(codigo: str) -> Optional[Turma]:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT codigo, curso_codigo, professor, horario, limite_vagas, vagas_ocupadas
        FROM turmas WHERE codigo=?
    """, (codigo,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    return Turma(row[0], row[1], row[2], row[3], row[4], row[5] or 0)

def aluno_por_matricula(m: str) -> Optional[Aluno]:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT matricula, nome FROM alunos WHERE matricula=?", (m,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    return Aluno(row[0], row[1])

# ----- util: parse horário e checar conflito -----
def parse_horario(h: str):
    """
    Espera formato: dia-ini-fim  (ex: seg-8-10)
    Retorna (dia, ini:int, fim:int)
    """
    try:
        dia, ini, fim = h.split("-")
        return dia.strip().lower(), int(ini), int(fim)
    except Exception:
        raise ValueError("Formato de horário inválido. Use dia-ini-fim, ex: seg-8-10")

def horarios_conflitam(h1: str, h2: str) -> bool:
    """
    Retorna True se horários conflitam.
    Considera mesmo 'dia' e intervalos numéricos [ini, fim)
    """
    try:
        dia1, ini1, fim1 = parse_horario(h1)
        dia2, ini2, fim2 = parse_horario(h2)
    except ValueError:
        # se formato inválido, assume conservadoramente que conflitam
        return True

    if dia1 != dia2:
        return False
    return max(ini1, ini2) < min(fim1, fim2)

# ----- pré-requisitos -----
def aluno_tem_prerequisitos(aluno_matricula: str, curso: Curso) -> bool:
    if not curso.prerequisitos:
        return True
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT t.curso_codigo
        FROM matriculas m
        JOIN turmas t ON t.codigo = m.turma_codigo
        WHERE m.aluno_matricula=? AND m.nota >= 6
    """, (aluno_matricula,))
    historico = {row[0] for row in cur.fetchall()}
    con.close()
    return all(pr in historico for pr in curso.prerequisitos)

# ----- matrícula -----
def matricular(aluno_matricula: str, turma_codigo: str) -> str:
    aluno = aluno_por_matricula(aluno_matricula)
    turma = turma_por_codigo(turma_codigo)

    if not aluno:
        return "❌ Erro: Aluno não encontrado."
    if not turma:
        return "❌ Erro: Turma não encontrada."

    curso = curso_por_codigo(turma.curso_codigo)
    if not curso:
        return "❌ Erro: Curso da turma não encontrado."

    con = conectar()
    cur = con.cursor()

    # 1. Matricula duplicada?
    cur.execute("SELECT 1 FROM matriculas WHERE aluno_matricula=? AND turma_codigo=?",
                (aluno_matricula, turma_codigo))
    if cur.fetchone():
        con.close()
        return "⚠ Aluno já está matriculado nesta turma."

    # 2. Já aprovado no curso?
    cur.execute("""
        SELECT t.curso_codigo FROM matriculas m
        JOIN turmas t ON t.codigo = m.turma_codigo
        WHERE m.aluno_matricula=? AND m.nota >= 6
    """, (aluno_matricula,))
    aprovados = {r[0] for r in cur.fetchall()}
    if curso.codigo in aprovados:
        con.close()
        return "⚠ Aluno já foi aprovado neste curso."

    # 3. Pré-requisitos
    if not aluno_tem_prerequisitos(aluno_matricula, curso):
        con.close()
        return "❌ Aluno não possui os pré-requisitos."

    # 4. Vagas
    if turma.vagas_ocupadas >= turma.limite_vagas:
        con.close()
        return f"❌ Turma sem vagas. (Limite: {turma.limite_vagas})"

    # 5. Conflito de horários
    cur.execute("""
        SELECT t.horario FROM matriculas m
        JOIN turmas t ON t.codigo = m.turma_codigo
        WHERE m.aluno_matricula=?
    """, (aluno_matricula,))
    horarios = [r[0] for r in cur.fetchall()]
    for h in horarios:
        if horarios_conflitam(h, turma.horario):
            con.close()
            return f"❌ Conflito de horário com turma no horário: {h}"

    # 6. Efetivar matrícula
    cur.execute("INSERT INTO matriculas (aluno_matricula, turma_codigo) VALUES (?,?)",
                (aluno_matricula, turma_codigo))
    cur.execute("UPDATE turmas SET vagas_ocupadas = vagas_ocupadas + 1 WHERE codigo=?",
                (turma_codigo,))
    con.commit()
    con.close()
    return "✅ Matrícula realizada com sucesso!"

# ----- registrar nota / frequência -----
def registrar_nota(matricula: str, turma: str, nota: float) -> str:
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE matriculas SET nota=? WHERE aluno_matricula=? AND turma_codigo=?",
                (nota, matricula, turma))
    con.commit()
    con.close()
    return "✔ Nota registrada."

def registrar_frequencia(matricula: str, turma: str, freq: float) -> str:
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE matriculas SET frequencia=? WHERE aluno_matricula=? AND turma_codigo=?",
                (freq, matricula, turma))
    con.commit()
    con.close()
    return "✔ Frequência registrada."

# ----- relatórios -----
def relatorio_historico(matricula: str):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT t.curso_codigo, m.nota, m.frequencia
        FROM matriculas m
        JOIN turmas t ON t.codigo = m.turma_codigo
        WHERE aluno_matricula=?
    """, (matricula,))
    dados = cur.fetchall()
    con.close()
    return dados

def calcular_cr(matricula: str) -> Optional[float]:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT m.nota FROM matriculas m
        WHERE m.aluno_matricula=? AND m.nota IS NOT NULL
    """, (matricula,))
    notas = [r[0] for r in cur.fetchall() if r[0] is not None]
    con.close()
    if not notas:
        return None
    return sum(notas) / len(notas)

# ============================
# CRUD: Cursos / Turmas / Alunos
# ============================
# --- Cursos ---
def criar_curso(codigo: str, nome: str, prerequisitos: List[str]) -> str:
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO cursos (codigo, nome, prerequisitos) VALUES (?,?,?)",
                    (codigo, nome, json.dumps(prerequisitos)))
        con.commit()
        return "✔ Curso criado."
    except sqlite3.IntegrityError:
        return "❌ Erro: já existe um curso com este código."
    finally:
        con.close()

def editar_curso(codigo: str, novo_nome: Optional[str], novos_prereq: Optional[List[str]]) -> str:
    curso = curso_por_codigo(codigo)
    if not curso:
        return "❌ Curso não encontrado."
    nome = novo_nome or curso.nome
    prereq = novos_prereq if novos_prereq is not None else curso.prerequisitos
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE cursos SET nome=?, prerequisitos=? WHERE codigo=?",
                (nome, json.dumps(prereq), codigo))
    con.commit()
    con.close()
    return "✔ Curso atualizado."

def excluir_curso(codigo: str) -> str:
    con = conectar()
    cur = con.cursor()
    # impedir exclusão se houver turmas
    cur.execute("SELECT 1 FROM turmas WHERE curso_codigo=?", (codigo,))
    if cur.fetchone():
        con.close()
        return "❌ Não é possível excluir: há turmas vinculadas a este curso."
    cur.execute("DELETE FROM cursos WHERE codigo=?", (codigo,))
    con.commit()
    con.close()
    return "✔ Curso excluído."

def listar_cursos():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT codigo, nome, prerequisitos FROM cursos ORDER BY codigo")
    linhas = cur.fetchall()
    con.close()
    resultados = []
    for c, n, p in linhas:
        prereq = json.loads(p) if p else []
        resultados.append(Curso(c, n, prereq))
    return resultados

# --- Turmas ---
def criar_turma(codigo: str, curso_codigo: str, professor: str, horario: str, limite_vagas: int) -> str:
    if not curso_por_codigo(curso_codigo):
        return "❌ Curso referenciado não existe."
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO turmas (codigo, curso_codigo, professor, horario, limite_vagas, vagas_ocupadas) VALUES (?,?,?,?,?,?)",
                    (codigo, curso_codigo, professor, horario, limite_vagas, 0))
        con.commit()
        return "✔ Turma criada."
    except sqlite3.IntegrityError:
        return "❌ Erro: já existe uma turma com este código."
    finally:
        con.close()

def editar_turma(codigo: str, novo_prof: Optional[str], novo_horario: Optional[str], novo_limite: Optional[int]) -> str:
    turma = turma_por_codigo(codigo)
    if not turma:
        return "❌ Turma não encontrada."
    prof = novo_prof or turma.professor
    horario = novo_horario or turma.horario
    limite = novo_limite if novo_limite is not None else turma.limite_vagas
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE turmas SET professor=?, horario=?, limite_vagas=? WHERE codigo=?",
                (prof, horario, limite, codigo))
    con.commit()
    con.close()
    return "✔ Turma atualizada."

def excluir_turma(codigo: str) -> str:
    con = conectar()
    cur = con.cursor()
    # impedir exclusão se houver matrículas
    cur.execute("SELECT 1 FROM matriculas WHERE turma_codigo=?", (codigo,))
    if cur.fetchone():
        con.close()
        return "❌ Não é possível excluir: há matrículas vinculadas a esta turma."
    cur.execute("DELETE FROM turmas WHERE codigo=?", (codigo,))
    con.commit()
    con.close()
    return "✔ Turma excluída."

def listar_turmas():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT codigo, curso_codigo, professor, horario, limite_vagas, vagas_ocupadas FROM turmas ORDER BY codigo")
    linhas = cur.fetchall()
    con.close()
    resultados = []
    for cod, curso, prof, hor, lim, ocup in linhas:
        resultados.append(Turma(cod, curso, prof, hor, lim, ocup or 0))
    return resultados

# --- Alunos ---
def criar_aluno(matricula: str, nome: str) -> str:
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO alunos (matricula, nome) VALUES (?,?)", (matricula, nome))
        con.commit()
        return "✔ Aluno criado."
    except sqlite3.IntegrityError:
        return "❌ Erro: já existe um aluno com esta matrícula."
    finally:
        con.close()

def editar_aluno(matricula: str, novo_nome: Optional[str]) -> str:
    aluno = aluno_por_matricula(matricula)
    if not aluno:
        return "❌ Aluno não encontrado."
    nome = novo_nome or aluno.nome
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE alunos SET nome=? WHERE matricula=?", (nome, matricula))
    con.commit()
    con.close()
    return "✔ Aluno atualizado."

def excluir_aluno(matricula: str) -> str:
    con = conectar()
    cur = con.cursor()
    # impedir exclusão se houver matrículas
    cur.execute("SELECT 1 FROM matriculas WHERE aluno_matricula=?", (matricula,))
    if cur.fetchone():
        con.close()
        return "❌ Não é possível excluir: o aluno possui matrículas."
    cur.execute("DELETE FROM alunos WHERE matricula=?", (matricula,))
    con.commit()
    con.close()
    return "✔ Aluno excluído."

def listar_alunos():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT matricula, nome FROM alunos ORDER BY matricula")
    linhas = cur.fetchall()
    con.close()
    resultados = []
    for m, n in linhas:
        resultados.append(Aluno(m, n))
    return resultados

# ============================
# CLI (menu)
# ============================
def menu():
    while True:
        print("\n=== MENU DO SISTEMA ACADÊMICO ===")
        print("1. Adicionar curso")
        print("2. Adicionar turma")
        print("3. Adicionar aluno")
        print("4. Matricular aluno")
        print("5. Registrar nota")
        print("6. Registrar frequência")
        print("7. Histórico do aluno")
        print("8. Editar curso")
        print("9. Excluir curso")
        print("10. Editar turma")
        print("11. Excluir turma")
        print("12. Editar aluno")
        print("13. Excluir aluno")
        print("14. Listar cursos")
        print("15. Listar turmas")
        print("16. Listar alunos")
        print("17. Calcular CR (aluno)")
        print("0. Sair")

        op = input("Escolha: ").strip()

        try:
            if op == "1":
                codigo = input("Código do curso: ").strip()
                nome = input("Nome: ").strip()
                prereq = input("Pré-requisitos (separados por vírgula) [vazio se nenhum]: ").strip()
                lista = [p.strip() for p in prereq.split(",") if p.strip()] if prereq else []
                print(criar_curso(codigo, nome, lista))

            elif op == "2":
                codigo = input("Código da turma: ").strip()
                curso = input("Código do curso: ").strip()
                prof = input("Professor: ").strip()
                horario = input("Horário (dia-ini-fim, ex: seg-8-10): ").strip()
                limite = int(input("Limite de vagas: ").strip())
                print(criar_turma(codigo, curso, prof, horario, limite))

            elif op == "3":
                matricula = input("Matrícula: ").strip()
                nome = input("Nome do aluno: ").strip()
                print(criar_aluno(matricula, nome))

            elif op == "4":
                m = input("Matrícula: ").strip()
                t = input("Turma: ").strip()
                print(matricular(m, t))

            elif op == "5":
                m = input("Matrícula: ").strip()
                t = input("Turma: ").strip()
                nota = float(input("Nota (0-10): ").strip())
                print(registrar_nota(m, t, nota))

            elif op == "6":
                m = input("Matrícula: ").strip()
                t = input("Turma: ").strip()
                freq = float(input("Frequência (0-100): ").strip())
                print(registrar_frequencia(m, t, freq))

            elif op == "7":
                m = input("Matrícula: ").strip()
                hist = relatorio_historico(m)
                print("\n=== HISTÓRICO ===")
                if not hist:
                    print("Nenhuma matrícula encontrada.")
                for c, n, f in hist:
                    print(f"Curso: {c} | Nota: {n} | Frequência: {f}")

            elif op == "8":
                codigo = input("Código do curso a editar: ").strip()
                novo_nome = input("Novo nome (deixe vazio para manter): ").strip() or None
                novos_pr = input("Novos pré-requisitos (vírgula) (deixe vazio para manter): ").strip()
                novos_prereq = [p.strip() for p in novos_pr.split(",") if p.strip()] if novos_pr else None
                print(editar_curso(codigo, novo_nome, novos_prereq))

            elif op == "9":
                codigo = input("Código do curso a excluir: ").strip()
                confirm = input("Confirma exclusão do curso? (s/n): ").strip().lower()
                if confirm == "s":
                    print(excluir_curso(codigo))
                else:
                    print("Operação cancelada.")

            elif op == "10":
                codigo = input("Código da turma a editar: ").strip()
                novo_prof = input("Novo professor (deixe vazio para manter): ").strip() or None
                novo_hor = input("Novo horário (dia-ini-fim) (deixe vazio para manter): ").strip() or None
                novo_lim = input("Novo limite de vagas (deixe vazio para manter): ").strip()
                novo_lim_val = int(novo_lim) if novo_lim else None
                print(editar_turma(codigo, novo_prof, novo_hor, novo_lim_val))

            elif op == "11":
                codigo = input("Código da turma a excluir: ").strip()
                confirm = input("Confirma exclusão da turma? (s/n): ").strip().lower()
                if confirm == "s":
                    print(excluir_turma(codigo))
                else:
                    print("Operação cancelada.")

            elif op == "12":
                m = input("Matrícula do aluno a editar: ").strip()
                novo_nome = input("Novo nome (deixe vazio para manter): ").strip() or None
                print(editar_aluno(m, novo_nome))

            elif op == "13":
                m = input("Matrícula do aluno a excluir: ").strip()
                confirm = input("Confirma exclusão do aluno? (s/n): ").strip().lower()
                if confirm == "s":
                    print(excluir_aluno(m))
                else:
                    print("Operação cancelada.")

            elif op == "14":
                cursos = listar_cursos()
                print("\n=== CURSOS ===")
                if not cursos:
                    print("Nenhum curso cadastrado.")
                for c in cursos:
                    print(f"Código: {c.codigo} | Nome: {c.nome} | Pré: {c.prerequisitos}")

            elif op == "15":
                turmas = listar_turmas()
                print("\n=== TURMAS ===")
                if not turmas:
                    print("Nenhuma turma cadastrada.")
                for t in turmas:
                    print(f"Código: {t.codigo} | Curso: {t.curso_codigo} | Prof: {t.professor} | Horário: {t.horario} | Vagas: {t.vagas_ocupadas}/{t.limite_vagas}")

            elif op == "16":
                alunos = listar_alunos()
                print("\n=== ALUNOS ===")
                if not alunos:
                    print("Nenhum aluno cadastrado.")
                for a in alunos:
                    print(f"Matrícula: {a.matricula} | Nome: {a.nome}")

            elif op == "17":
                m = input("Matrícula: ").strip()
                cr = calcular_cr(m)
                if cr is None:
                    print("Sem notas para calcular CR.")
                else:
                    print(f"CR: {cr:.2f}")

            elif op == "0":
                print("Encerrado.")
                break

            else:
                print("Opção inválida.")

        except Exception as e:
            print(f"Erro: {e}")

# ============================
# Entrypoint
# ============================
if __name__ == "__main__":
    inicializar()
    print("Sistema carregado! Execute o menu para iniciar.")
    menu()
