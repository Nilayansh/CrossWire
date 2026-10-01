.PHONY: test lint run-api run-ui clean

test:
	python -m pytest tests -q

test-p0:
	python -m pytest tests/P0 -v

lint:
	python -m flake8 app tests --max-line-length=120 || true

run-api:
	python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	streamlit run ui/streamlit_app.py

run-ui-mock:
	USE_MOCK_API=1 streamlit run ui/streamlit_app.py

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
