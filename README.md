# 📘 **README – Sistema Acadêmico**

---
## CURSO ANALISE E DESENVOLVIMENTO DE SISTEMAS - PROGRAMAÇÃO ORIENTADA OBJETO (PROJETO FINAL)

**ALUNOS**: :rocket:
* Francisco Airton Araujo Junior - 2023010960
* Francisco Eduardo da Silva - 2023009600
* Ismael Gomes da Silva - 2023011143
* Rodrigo Bezerra Nunes - 2023018707


Sistema acadêmico simples e funcional desenvolvido em **Python**, com persistência em **SQLite**, seguindo boas práticas de **Programação Orientada a Objetos**, uso de **dataclasses**, serviços organizados e uma interface **CLI**.

---

# 📂 Estrutura do Projeto

```
sistema-academico/
│
├── src/
│   └── sistema_academico.py
│
├── database/
│   └── gestor_academico.db   ← gerado automaticamente
│
├── README.md
└── RELATORIO.md

```

---

# 🧩 Tecnologias Utilizadas

- Python 3.10+
- Dataclasses
- SQLite3
- JSON
- CLI (Input padrão)
- Arquitetura em camadas

---

# 🏗️ Arquitetura do Sistema

O projeto segue uma estrutura modular:

### **1. Modelos (Camada de Dados)**

Implementados com `dataclasses`.

- `Curso`
- `Turma`
- `Aluno`
- `Matricula`

### **2. Serviços (Regras de Negócio)**

Funções responsáveis por:

- Validação de pré-requisitos
- Controle de vagas
- Choque de horário
- Registro de notas
- Registro de frequência
- Geração de histórico

### **3. Persistência**

- Banco SQLite criado automaticamente
- Consultas centralizadas
- JSON para armazenar listas de pré-requisitos

### **4. Interface CLI**

Menu simples e funcional para operação direta.

---

# 🧱 Principais Classes

### ✔ **EntidadeBase**

Superclasse usada para facilitar debug e impressão estruturada.

### ✔ **Curso**

Representa um curso com código, nome e pré-requisitos.

### ✔ **Turma**

Oferta do curso com professor, horário e limite de vagas.

### ✔ **Aluno**

Estudante matriculado no sistema.

### ✔ **Matricula**

Relaciona `Aluno` ↔ `Turma`, contendo nota e frequência.

---

# 🧠 Regras de Negócio Implementadas

- ✔ Verificação de pré-requisitos
- ✔ Detecção de choque de horário
- ✔ Controle de vagas ocupadas
- ✔ Registro de notas e frequência
- ✔ Histórico completo do aluno
- ✔ Estrutura segura com validações obrigatórias

---

# ▶️ Como Executar o Sistema

### **1. Clonar o repositório**

```bash
git clone https://github.com/airtonjunior2016/sis_academico.git

```

### **2. Rodar o sistema**

```bash
python3 sistema_academico.py

```

### **3. Abrir o menu**

Dentro do programa:

```
menu()

```

---

# 📚 Menu do Sistema```
1. Adicionar curso
2. Adicionar turma
3. Adicionar aluno
4. Matricular aluno
5. Registrar nota
6. Registrar frequência
7. Histórico do aluno
8. Editar curso
9. Excluir curso
10. Editar turma
11. Excluir turma
12. Editar aluno
13. Excluir aluno
14. Listar cursos
15. Listar turmas
16. Listar alunos
17. Calcular CR (aluno)
0. Sair

```

---

# 🗄️ Banco de Dados

O sistema gera automaticamente o arquivo:

```
database/gestor_academico.db

```

Não é necessário configurar nada.

---

# 📄 Licença

Este projeto está licenciado sob a **MIT License** – uso livre para fins acadêmicos, profissionais e aprendizado.
