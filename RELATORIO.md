📚 Sistema Acadêmico – Relatório Técnico

RELATÓRIO TÉCNICO: SISTEMA DE GESTÃO ACADÉMICA
Autores: Airton Junior, Francisco Eduardo, 
Disciplina: Programação Orientada a Objetos 


1. INTRODUÇÃO

O presente projeto tem como objetivo o desenvolvimento de um Sistema de Gestão Acadêmica (SisAcademico), uma aplicação desenvolvida para automatizar e organizar os processos fundamentais de uma instituição de ensino.

A gestão manual de matrículas, turmas e notas é propensa a falhas humanas, como conflitos de horários ou matrículas indevidas. Este software visa mitigar esses erros através de um sistema robusto de validação de dados, utilizando a linguagem Python e persistência em base de dados relacional. O foco central do desenvolvimento não foi apenas o cadastro (CRUD), mas a garantia da integridade referencial e a aplicação estrita das regras de negócio académicas.

2. OBJETIVOS

2.1 Objetivo Geral
Desenvolver uma aplicação em linha de comandos (CLI) que permita o controlo total do ciclo de vida acadêmico: desde a criação de cursos até à emissão de históricos escolares.

2.2 Objetivos Específicos

Implementar persistência de dados eficiente utilizando SQLite.

Aplicar conceitos de Orientação a Objetos para modelagem de entidades.

Desenvolver algoritmos de validação para impedir matrículas inválidas (conflitos de horário, falta de pré-requisitos, turmas cheias).

Gerar relatórios de desempenho (Cálculo de Coeficiente de Rendimento - CR).

3. TECNOLOGIAS E ARQUITETURA
3.1 Ferramentas Utilizadas
Linguagem: Python 3.14x (pela sua legibilidade e suporte nativo a SQLite).

Banco de Dados: SQLite3 (base de dados serverless, ideal para aplicações locais).

Bibliotecas Auxiliares:

dataclasses: Para redução de boilerplate na criação de objetos.

json: Para serialização de estruturas de dados complexas (listas) dentro do banco relacional.

3.2 Arquitetura de Software

O sistema adota uma arquitetura modular implícita, separando as responsabilidades em três camadas lógicas:

1. Modelo (Models): Representado pelas dataclasses (Curso, Turma, Aluno), que definem a estrutura dos dados em memória.

2. Persistência (Database): Funções responsáveis pela conexão, criação de tabelas e execução de queries SQL seguras (uso de placeholders para prevenir Injeção de SQL).

3. Regras de Negócio (Services): O núcleo lógico onde ocorrem as validações (ex: matricular, verificar_conflito).

4. MODELAGEM DE DADOS

erDiagram
    CURSOS ||--o{ TURMAS : "gera"
    TURMAS ||--o{ MATRICULAS : "possui"
    ALUNOS ||--o{ MATRICULAS : "realiza"

    CURSOS {
        TEXT codigo PK "Chave Primária"
        TEXT nome
        TEXT prerequisitos "JSON (Lista serializada)"
    }

    TURMAS {
        TEXT codigo PK "Chave Primária"
        TEXT curso_codigo FK "Ref. Cursos"
        TEXT professor
        TEXT horario
        INTEGER limite_vagas
        INTEGER vagas_ocupadas
    }

    ALUNOS {
        TEXT matricula PK "Chave Primária"
        TEXT nome
    }

    MATRICULAS {
        INTEGER id PK "Autoincremento"
        TEXT aluno_matricula FK "Ref. Alunos"
        TEXT turma_codigo FK "Ref. Turmas"
        REAL nota
        REAL frequencia
    }


ENTIDADE RELACIONAMENTO - DIAGRAMA

![alt text](image.png)

O banco de dados gestor_academico.db foi estruturado com as seguintes entidades relacionais:

CURSOS: Armazena o código, nome e pré-requisitos (serializados em JSON).

TURMAS: Vincula um professor e horário a um curso, controlando o limite de vagas.

ALUNOS: Registo cadastral dos discentes.

MATRICULAS: Tabela associativa que liga Alunos a Turmas, contendo também os atributos de relação nota e frequência.

5. IMPLEMENTAÇÃO E REGRAS DE NEGÓCIO

O diferencial técnico deste projeto reside no algoritmo de matrícula (def matricular). Diferente de um cadastro simples, o sistema executa um funil de validação rigoroso antes de efetivar qualquer registro:

1. Verificação de Existência: Garante que aluno e turma estão registados no banco.

2. Unicidade: Impede que um aluno se matricule duas vezes na mesma turma.

3. Histórico Acadêmico: Verifica se o aluno já foi aprovado na disciplina anteriormente.

4. Pré-requisitos Recursivos: Analisa o histórico do aluno para assegurar que todas as disciplinas obrigatórias anteriores foram concluídas com êxito.

5. Controle de Vagas: Consulta o campo vagas_ocupadas versus limite_vagas em tempo real.

6. Detecção de Conflitos de Horário:

Foi desenvolvido um parser personalizado (parse_horario) que converte strings de horário (ex: "seg-8-10") em dados numéricos.

A função verifica matematicamente se há sobreposição de intervalos entre a nova turma e as turmas onde o aluno já está inscrito.

6. DESAFIOS E SOLUÇÕES TÉCNICAS

Desafio: O SQLite não possui um tipo de dado nativo para armazenar listas (necessário para os pré-requisitos dos cursos). Solução: Implementou-se uma estratégia de serialização utilizando a biblioteca json. Ao gravar no banco, a lista de pré-requisitos é convertida em string (json.dumps); ao ler do banco, é reconvertida em lista Python (json.loads). Isso permitiu manter a flexibilidade da orientação a objetos dentro de um banco relacional rígido.

7. CONCLUSÃO E TRABALHOS FUTUROS
O sistema desenvolvido cumpre com êxito os requisitos de gestão académica, oferecendo uma interface segura e validada para a manipulação de dados sensíveis. O uso de SQLite garantiu a portabilidade da aplicação, enquanto a Orientação a Objetos facilitou a manipulação das entidades.

Para versões futuras, sugere-se:

1. Implementação de uma Interface Gráfica (GUI) para melhor experiência do utilizador.

2. Adição de um sistema de login com níveis de acesso (Administrador vs. Aluno).

3. Implementação de "exclusão em cascata" (Cascade Delete) no banco de dados para integridade referencial automática.