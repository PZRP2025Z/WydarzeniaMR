# Aplikacja do organizacji prywatnych wydarzeń
*Członkowie Zespołu*: Błażej Michalak, Wojciech Sarwiński, Maciej Scheffer

Celem projektu jest stworzenie aplikacji internetowej, która będzie pozwalała na organizację prywatnych wydarzeń. W ramach wydarzenia użytkowicy mogą wstawiać komentarze pod wydarzeniem i brać udział w ankietach. Dla ułatwienia adopcji, żeby dołączyć do spotkania użytkowicy mogą dołączyć przy pomocy linków spersonalizowanych lub ogólnych, bez konieczności zakładania konta. Członkowie wydarzenia mogą zgodzić się na otrzymywanie przez mail lub web push powiadomień o zmianach informacji o wydarzeniu czy informacji o uczestnictwie. Projekt zakłada też przygotowanie aplikacji do obsługi wielu języków na przykładzie obsługi języka polskiego i angielskiego.

# Harmonogram

27.10 - Start Projektu

- Minimalistyczny funkcjonujący frontend
- Tabela wydarzeń w bazie danych
- Dodanie nowego wydarzenia przez API
- Logger
- Przygotowanie do internacjonalizacji
- Automatyzacja budowania i testowania
- Kontenryzacja
- Podstawowe testy kodu
- Ustawienie środowiska: linter i autoformater - ruff

03.11 - Rejestracja i Logowanie

- Interfejs logowania i tworzenia konta
- Dodawanie konta do bazy danych
- Kolejkowanie Dramatiq

10.11 - Tworzenie wydarzenia

- Interfejs tworzenia wydarzenia
- Widok wydarzenia
- Edytowanie opisu wydarzenia / daty rozpoczęcia / zdjęcia
- Obsługa MarkDown

17.11 - Genrowanie linków
- Cookies automatycznie logujące zarejestrowanego użytkownika 
- Anonimowe linki wymagające podania podstawowych danych niezarejestrowanym użytkonikom oraz opcjonalnemu zalogowaniu się
- Personalizowane linki
- Interfejs wprowadzania kodu / logowania się

24.11 - Sekcja Komentarzy
- Interfejs sekcji komentarzy
- Dodawanie komentarzy
- Rejestrowanie komentarzy w bazie danych
- Paginacja i cache

01.12 - Powiadomienia
- Powiadomienia Email
- Powiadomienia Whatsapp
- Powiadomienia WebPush

08.12 - Main Page 
- Widok wszystkich wydarzeń użytkownika po zalogowaniu
- Widok niezalogowanego użytkownika

15.12 - Tworzenie ankiet
- Interfejs tworzenia ankiety
- Przesyłanie głosów przez użytkowników
- Wizualizacja wyników ankiety

22.12 - Przerwa Świąteczna

29.12 - Dodatkowe
- Dodanie wydarzenia do kalendarza Google
- Widok zarządzania kontem
- Testowanie API

05.01 - Gotowy Projekt
- Ostatnie poprawki i odesłanie projektu

Deadline: 15.01

# Planowana Funkcjonalność
*Wymagania funkcjonalne:*
- Tworzenie wydarzeń
    - Obsługa MarkDown w opisie wydarzenia
    - Ustawianie własnego zdjęcia wydarzenia
- Listowanie wydarzeń
- Możliwość korzystania z aplikacji z kontem i bez konta
  - Tworzenie wydarzeń wymaga założenia konta
  - Dołączanie wymaga tylko imienia
- Możliwość zapraszania do wydarzenia poprzez link
    - Weryfikacja poprzez spersonalizowany link oraz kod wstępu
    - Możliwość wysłania niespersonalizowanego linka, wymagającego wprowadzenia dodatkowych danych użytkownika
- Powiadamianie użytkowników poprzez email oraz Web Push, w przypadku
  - Zmiany opisu wydarzenia
  - Zmiany terminu wydarzenia
  - Zaproszenia na wydarzenia
  - Powiadomienia o uczestnictwie
- Możliwość dodawania komentarzy przez użytkowników
- Możliwość dodania wydarzenia do kalendarza Google
- Przygotowanie do internacjonalizacji, na przykładzie języka polskiego i angielskiego
- Tworzenie ankiet
  - Z natychmiastowymi procentowymi wynikami
  - Z terminowym ogłoszeniem wyników

*Wymagania niefunkcjonalne:*
 - 90% Pokrycie kodu testami: pytest, httpx, hypothesis
 - Możliwość uruchomienia stosu za pomocą Docker Compose
 - Mechanizmy logowania: logging
 - Kolejkowanie i cache : Dramatiq, Redis
 - Ustawienie środowiska: linter i autoformater - ruff
 - Typowanie - Pydantic
 - Konteneryzacja: docker-compose
 - Automatyzacja budowania i testowania: Make

# Planowany stack technologiczny
- *Backend*: FastAPI, Dramatiq, Logging, Redis, SQLModel
- *Frontend*: Svelte, Skeleton
- *Baza danych*: PostgreSq

# Bibliografia
- [FastAPI](https://fastapi.tiangolo.com/reference/)
- [Dramatiq](https://dramatiq.io/index.html)
- [Logging](https://docs.python.org/3/library/logging.html)
- [Redis](https://redis.io/docs/latest/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Svelte](https://svelte.dev/docs)
- [Skeleton](https://www.skeleton.dev/)
- [Postgresql](https://www.postgresql.org.pl/)
