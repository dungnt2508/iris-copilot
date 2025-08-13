# DDD Architecture Guide cho IRIS Backend

## 1. Bounded Contexts trong IRIS

### Identity & Access Management (IAM)
```
Domain: Quản lý người dùng, xác thực, phân quyền
Entities: User, Role, Permission, Session
Aggregate Root: User
```

### Content Management (CM)
```
Domain: Quản lý tài liệu, xử lý nội dung
Entities: Document, DocumentChunk, DocumentVersion
Aggregate Root: Document
```

### Chat & Conversation (CC)
```
Domain: Quản lý hội thoại, AI responses
Entities: Conversation, Message, Response
Aggregate Root: Conversation
```

### Embedding & Search (ES)
```
Domain: Vector embeddings, semantic search
Entities: Embedding, SearchIndex, SearchResult
Aggregate Root: Embedding
```

## 2. Aggregate Design

### User Aggregate
```python
class UserAggregate:
    """
    User Aggregate - đảm bảo consistency của user data
    """
    def __init__(self, user: User):
        self.user = user  # Aggregate Root
        self.profile = UserProfile(user.id)
        self.permissions = []
        self.sessions = []
    
    def register_user(self, email: str, password: str, full_name: str):
        """Business operation: đăng ký user mới"""
        # 1. Validate input
        if not self._validate_registration_data(email, password, full_name):
            raise ValueError("Invalid registration data")
        
        # 2. Check existing user
        if self._user_exists(email):
            raise ValueError("User already exists")
        
        # 3. Create user with default settings
        self.user = User.create(
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.USER,
            status=UserStatus.PENDING
        )
        
        # 4. Create default profile
        self.profile = UserProfile.create_for_user(self.user.id)
        
        # 5. Set default permissions
        self.permissions = self._get_default_permissions(UserRole.USER)
        
        # 6. Commit to repository (atomic operation)
        self.repository.save_aggregate(self)
    
    def update_role(self, new_role: UserRole, updated_by: User):
        """Business operation: cập nhật role"""
        # 1. Check permissions
        if not updated_by.can_manage_user():
            raise PermissionError("Insufficient permissions")
        
        # 2. Update user role
        self.user.update_role(new_role)
        
        # 3. Update permissions accordingly
        self.permissions = self._get_permissions_for_role(new_role)
        
        # 4. Invalidate existing sessions
        self._invalidate_sessions()
        
        # 5. Commit changes
        self.repository.save_aggregate(self)
    
    def authenticate(self, email: str, password: str) -> Session:
        """Business operation: xác thực user"""
        # 1. Verify credentials
        if not self.user.verify_password(password):
            raise ValueError("Invalid credentials")
        
        # 2. Check account status
        if not self.user.is_active():
            raise ValueError("Account is not active")
        
        # 3. Create new session
        session = Session.create_for_user(self.user.id)
        self.sessions.append(session)
        
        # 4. Update last login
        self.user.update_last_login()
        
        # 5. Commit changes
        self.repository.save_aggregate(self)
        
        return session
```

### Document Aggregate
```python
class DocumentAggregate:
    """
    Document Aggregate - đảm bảo consistency của document data
    """
    def __init__(self, document: Document):
        self.document = document  # Aggregate Root
        self.chunks = []
        self.embeddings = []
        self.versions = []
    
    def upload_and_process(self, file_content: bytes, filename: str, user_id: str):
        """Business operation: upload và xử lý document"""
        # 1. Validate file
        if not self._validate_file(file_content, filename):
            raise ValueError("Invalid file")
        
        # 2. Create document
        self.document = Document.create(
            filename=filename,
            user_id=user_id,
            status=DocumentStatus.PROCESSING
        )
        
        # 3. Process content
        content = self._extract_content(file_content)
        chunks = self._chunk_content(content)
        
        # 4. Create chunks
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk.create(
                document_id=self.document.id,
                content=chunk_content,
                order_index=i
            )
            self.chunks.append(chunk)
        
        # 5. Generate embeddings
        for chunk in self.chunks:
            embedding = Embedding.create_for_chunk(chunk.id, chunk.content)
            self.embeddings.append(embedding)
        
        # 6. Create version
        version = DocumentVersion.create(
            document_id=self.document.id,
            version_number=1,
            chunks_count=len(self.chunks)
        )
        self.versions.append(version)
        
        # 7. Update document status
        self.document.mark_as_processed()
        
        # 8. Commit to repository (atomic operation)
        self.repository.save_aggregate(self)
    
    def search_similar(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Business operation: tìm kiếm tương tự"""
        # 1. Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # 2. Find similar embeddings
        similar_embeddings = self._find_similar_embeddings(
            query_embedding, 
            limit
        )
        
        # 3. Get corresponding chunks
        chunks = [emb.chunk for emb in similar_embeddings]
        
        # 4. Create search results
        results = []
        for chunk in chunks:
            result = SearchResult.create(
                chunk=chunk,
                similarity_score=chunk.similarity_score,
                document=self.document
            )
            results.append(result)
        
        return results
```

## 3. Repository Pattern cho Aggregates

### User Repository
```python
class UserRepository(ABC):
    @abstractmethod
    async def save_aggregate(self, aggregate: UserAggregate) -> UserAggregate:
        """Save entire user aggregate atomically"""
        pass
    
    @abstractmethod
    async def find_aggregate_by_id(self, user_id: str) -> Optional[UserAggregate]:
        """Find user aggregate by ID"""
        pass
    
    @abstractmethod
    async def find_aggregate_by_email(self, email: str) -> Optional[UserAggregate]:
        """Find user aggregate by email"""
        pass
```

### Document Repository
```python
class DocumentRepository(ABC):
    @abstractmethod
    async def save_aggregate(self, aggregate: DocumentAggregate) -> DocumentAggregate:
        """Save entire document aggregate atomically"""
        pass
    
    @abstractmethod
    async def find_aggregate_by_id(self, document_id: str) -> Optional[DocumentAggregate]:
        """Find document aggregate by ID"""
        pass
    
    @abstractmethod
    async def find_aggregates_by_user(self, user_id: str) -> List[DocumentAggregate]:
        """Find all document aggregates for user"""
        pass
```

## 4. Use Cases với Aggregates

### User Use Cases
```python
class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, email: str, password: str, full_name: str) -> User:
        # 1. Create empty aggregate
        user = User.create_empty()
        aggregate = UserAggregate(user)
        
        # 2. Execute business operation
        aggregate.register_user(email, password, full_name)
        
        # 3. Save to repository
        saved_aggregate = await self.user_repository.save_aggregate(aggregate)
        
        return saved_aggregate.user

class LoginUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, email: str, password: str) -> Session:
        # 1. Find user aggregate
        aggregate = await self.user_repository.find_aggregate_by_email(email)
        if not aggregate:
            raise ValueError("User not found")
        
        # 2. Execute business operation
        session = aggregate.authenticate(email, password)
        
        # 3. Save to repository
        await self.user_repository.save_aggregate(aggregate)
        
        return session
```

### Document Use Cases
```python
class UploadDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
    
    async def execute(self, file_content: bytes, filename: str, user_id: str) -> Document:
        # 1. Create empty aggregate
        document = Document.create_empty()
        aggregate = DocumentAggregate(document)
        
        # 2. Execute business operation
        aggregate.upload_and_process(file_content, filename, user_id)
        
        # 3. Save to repository
        saved_aggregate = await self.document_repository.save_aggregate(aggregate)
        
        return saved_aggregate.document

class SearchDocumentsUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
    
    async def execute(self, query: str, user_id: str, limit: int = 10) -> List[SearchResult]:
        # 1. Get user's documents
        aggregates = await self.document_repository.find_aggregates_by_user(user_id)
        
        # 2. Search in each aggregate
        all_results = []
        for aggregate in aggregates:
            results = aggregate.search_similar(query, limit)
            all_results.extend(results)
        
        # 3. Sort by relevance
        all_results.sort(key=lambda r: r.similarity_score, reverse=True)
        
        return all_results[:limit]
```

## 5. Benefits cho IRIS

### A. Data Consistency
- User data luôn consistent (role + permissions + sessions)
- Document data luôn consistent (document + chunks + embeddings)

### B. Business Rules Encapsulation
- Business rules được đóng gói trong Aggregate
- Không thể bypass business rules

### C. Transaction Safety
- Thay đổi trong Aggregate là atomic
- Rollback tự động nếu có lỗi

### D. Scalability
- Dễ dàng tách thành microservices
- Mỗi Bounded Context có thể scale độc lập

### E. Maintainability
- Code rõ ràng, dễ hiểu
- Dễ test và debug
- Dễ thêm features mới

## 6. Migration Path

### Phase 1: Refactor Existing Code
1. Tạo Aggregate classes
2. Move business logic vào Aggregates
3. Update Use Cases để sử dụng Aggregates

### Phase 2: Add New Features
1. Implement new Aggregates cho features mới
2. Add Repository implementations
3. Add Use Cases

### Phase 3: Microservices Preparation
1. Separate Bounded Contexts
2. Add inter-context communication
3. Implement event-driven architecture
