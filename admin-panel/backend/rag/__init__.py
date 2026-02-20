import os
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import PyPDF2
import docx
import time


class RAGSystem:
    """
    سیستم RAG برای هر گروه با ChromaDB و OpenRouter Embeddings
    """

    def __init__(
        self,
        group_id: int,
        api_key: str,
        base_url: Optional[str] = "https://openrouter.ai/api/v1",
        embedding_model: str = "openai/text-embedding-3-small",
    ):
        self.group_id = group_id
        self.api_key = api_key
        self.base_url = base_url
        self.embedding_model = embedding_model

        self.collection_name = f"group_{group_id}_documents"
        self.persist_directory = Path(f"backend/chroma_db/group_{group_id}")
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # اتصال به ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # ساخت یا بارگذاری collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✅ Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            print(f"✅ Created new collection: {self.collection_name}")

        # ساخت OpenAI Client برای Embeddings، سازگار با OpenRouter
        self.openai_client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=0.4,
            max_retries=3,
        )

        print(f"🔧 RAG System initialized for Group {group_id}")
        print(f"   Collection: {self.collection_name}")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   Persist Directory: {self.persist_directory}")

    # ------------------- File Extraction --------------------

    def _extract_text_from_pdf(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise RuntimeError(f"Error extracting PDF: {e}")

    def _extract_text_from_docx(self, file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            raise RuntimeError(f"Error extracting DOCX: {e}")

    def _extract_text_from_txt(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        except Exception as e:
            raise RuntimeError(f"Error extracting TXT: {e}")

    def _validate_file(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if path.suffix.lower() not in [".pdf", ".docx", ".txt"]:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    # ------------------- Text Chunking --------------------

    def _chunk_text(self, text: str, chunk_size: int = 350, overlap: int = 50) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            if len(chunk.strip()) > 50:
                chunks.append(chunk.strip())
            start = end - overlap
        return chunks

    # ------------------- Embedding Operations --------------------

    def _get_embeddings_batch(self, texts: List[str], batch_size: int = 350) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                print(f"   Processed batch {i // batch_size + 1}")
            except Exception as e:
                raise RuntimeError(f"Embedding batch failed: {e}")
        return embeddings

    def _get_embedding(self, text: str) -> List[float]:
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}")

    # ------------------- Document Operations --------------------

    async def add_document(self, file_path: str) -> int:
        print(f"\n📄 Processing document: {file_path}")
        self._validate_file(file_path)

        ext = Path(file_path).suffix.lower()
        text = (
            self._extract_text_from_pdf(file_path)
            if ext == ".pdf"
            else self._extract_text_from_docx(file_path)
            if ext == ".docx"
            else self._extract_text_from_txt(file_path)
        )

        print(f"   Extracted text length: {len(text)} characters")

        chunks = self._chunk_text(text)
        print(f"   Created {len(chunks)} chunks")

        embeddings = self._get_embeddings_batch(chunks)
        filename = Path(file_path).name

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            self.collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[
                    {
                        "filename": filename,
                        "chunk_index": i,
                        "group_id": self.group_id,
                    }
                ],
                ids=[f"{filename}_chunk_{i}"],
            )

        print(f"✅ Document added successfully ({len(chunks)} chunks)")
        return len(chunks)

    def delete_document(self, filename: str) -> None:
        """
        حذف تمام embeddingهای مربوط به یک سند خاص بر اساس نام فایل.
        """
        try:
            existing_count = self.collection.count()
            print(f"🧾 Current chunk count before delete: {existing_count}")

            deleted = self.collection.delete(where={"filename": filename})
            print(f"🗑️ Deleted embeddings for {filename}")

            new_count = self.collection.count()
            print(f"📈 Remaining chunks after delete: {new_count}")
            if existing_count == new_count:
                print(f"⚠️ Warning: No chunks found for {filename}")
        except Exception as e:
            print(f"❌ Error deleting document embeddings: {e}")

    def search(self, query: str, top_k: int = 3) -> List[str]:
        

        print("🟢🟢🟢 NEW DEBUG VERSION RUNNING 🟢🟢🟢")
        print(f"\n🔍 === SEARCH DEBUG START ===")

        # Step 1: Check collection
        t0 = time.time()
        count = self.collection.count()
        t1 = time.time()
        print(f"⏱️ Step 1 - Collection count ({count} chunks): {(t1-t0)*1000:.1f}ms")

        if count == 0:
            print("⚠️ Collection is EMPTY!")
            return []

        # Step 2: Get embedding
        try:
            t2 = time.time()
            query_embedding = self._get_embedding(query)
            t3 = time.time()
            print(f"⏱️ Step 2 - _get_embedding(): {(t3-t2)*1000:.1f}ms")
        except Exception as e:
            print(f"❌ Step 2 CRASHED: {e}")
            return []

        if query_embedding is None:
            print("❌ Embedding returned None!")
            return []

        print(f"   Embedding length: {len(query_embedding)}")

        # Step 3: ChromaDB query
        try:
            t4 = time.time()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
            t5 = time.time()
            print(f"⏱️ Step 3 - ChromaDB query: {(t5-t4)*1000:.1f}ms")
        except Exception as e:
            print(f"❌ Step 3 CRASHED: {e}")
            return []

        # Step 4: Process results
        t6 = time.time()
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [None] * len(docs)

            combined = []
            for doc, meta, dist in zip(docs, metas, distances):
                filename = meta.get("filename", "unknown") if meta else "unknown"
                similarity = f"{1 - dist:.2f}" if dist is not None else "N/A"
                preview = doc[:200] + ("..." if len(doc) > 200 else "")
                combined.append(f"[{filename} | sim: {similarity}] {preview}")
                print(f"   ✅ Found: {filename} (similarity: {similarity})")

            t7 = time.time()
            print(f"⏱️ Step 4 - Process results: {(t7-t6)*1000:.1f}ms")
            print(f"⏱️ TOTAL SEARCH TIME: {(t7-t0)*1000:.1f}ms")
            print(f"🔍 === SEARCH DEBUG END ===\n")
            return combined

        print("⚠️ No results returned")
        print(f"🔍 === SEARCH DEBUG END ===\n")
        return []

    
    


    def load_existing(self) -> bool:
        try:
            count = self.collection.count()
            print(f"📊 Found {count} documents in collection")
            return count > 0
        except Exception:
            return False

    def clear(self) -> None:
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"🗑️ Cleared collection: {self.collection_name}")
        except Exception as e:
            print(f"⚠️ Error clearing collection: {e}")

    def get_stats(self) -> dict:
        try:
            count = self.collection.count()
            return {
                "group_id": self.group_id,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model,
                "total_chunks": count,
                "persist_directory": str(self.persist_directory),
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
