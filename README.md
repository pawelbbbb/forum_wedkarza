# Forum Wędkarskie

Projekt forum dyskusyjnego napisany w Pythonie (Flask) i wdrożony w chmurze AWS w ramach kursu Bezpieczeństwo serwerów i aplikacji Web.



Aplikacja umożliwia rejestrację i logowanie użytkowników, tworzenie postów oraz dodawanie komentarzy.
Dane przechowywane są w bazie MariaDB na Amazon RDS.



System został wdrożony w architekturze chmurowej z użyciem kontenerów Docker uruchamianych w Amazon ECS.
Ruch HTTPS obsługiwany jest przez Load Balancer z certyfikatem TLS.



W projekcie zastosowano podstawowe mechanizmy bezpieczeństwa, m.in.:

* hashowanie haseł (bcrypt)
* ochronę CSRF
* nagłówki bezpieczeństwa
* AWS WAF
* skanowanie podatności w procesie CI/CD (Semgrep, OWASP ZAP)