# MDO-UNESP

Projeto de Otimização Multidisciplinar (MDO) desenvolvido no contexto da UNESP.

## 🚀 Instalação

Para configurar o ambiente de desenvolvimento e instalar esta biblioteca localmente, siga os passos abaixo.

### 1\. Pré-requisitos

- [Python 3.9+](https://www.python.org/)
- [Git](https://git-scm.com/)
- `pip` (geralmente incluído no Python)

### 2\. Clonar o Repositório

Primeiro, clone o repositório para a sua máquina local:

```bash
git clone https://github.com/seu-usuario/MDO-UNESP.git
cd MDO-UNESP
```

### 3\. Ambiente Virtual (Recomendado)

É uma boa prática criar um ambiente virtual para isolar as dependências do projeto:

```bash
# Criar o ambiente
python -m venv env

# Ativar o ambiente
# No Windows (PowerShell):
.\env\Scripts\Activate.ps1
# No macOS/Linux:
source env/bin/activate
```

### 4\. Instalar a Biblioteca

Com o ambiente ativo, instale a biblioteca em **modo editável**:

```bash
pip install -e .
```

> **Por que usar `-e .`?**
> A flag `-e` (de _editable_) instala o pacote criando um link para o seu código-fonte. Isso significa que qualquer alteração que você fizer nos arquivos `.py` será refletida imediatamente no pacote instalado, sem a necessidade de reinstalá-lo.

---

## 🧪 Rodando os Testes

Após a instalação, você pode verificar se tudo está funcionando corretamente rodando a suíte de testes (é necessário ter o `pytest` instalado):

```bash
# Instalar o pytest (se ainda não o fez)
pip install pytest

# Executar os testes
pytest
```
