---
title: "Demo Project Osmos w Microsoft Fabric"
subtitle: "Surowe pliki sprzedaży detalicznej, z których agent buduje architekturę medalionową"
lang: pl-PL
toc-title: "Spis treści"
---

# Demo Project Osmos w Microsoft Fabric

[English version](README.md)

To repozytorium opisuje przykładowy workspace, na którym można pokazać Project Osmos w praktyce. W Lakehouse leżą surowe pliki CSV z fikcyjnej sieci sklepów. Są celowo zabrudzone, bo właśnie na takim materiale widać, że agent sam rozpoznaje dane, pisze i uruchamia kod Spark, poprawia go po błędach i zostawia po sobie notebooki oraz tabele Delta.

Zadanie Osmos nie zostało jeszcze uruchomione. Wszystko jest przygotowane tak, żeby wystartować je w trakcie prezentacji.

## Czym jest Project Osmos

Według opisu produktu dołączonego do skilla `project-osmos` (Microsoft Skills for Fabric) to długo działający agent inżynierii danych dla Fabric. Dostaje opis oczekiwanego wyniku, a nie listę kroków. Potrafi przejrzeć dane, napisać i uruchomić kod Spark, utworzyć i przetestować notebooki, wyczyścić i przekształcić dane oraz utworzyć lub zaktualizować tabele Delta. Całość prowadzi jako jedno zadanie widoczne w portalu Fabric. W razie wątpliwości może zatrzymać się i zadać pytanie.

Lakehouse wskazany przy starcie zadania służy tylko do uruchomienia sesji Spark w odpowiednim workspace i na jego capacity. Nie ogranicza tego, co agent może czytać ani gdzie zapisze wyniki.

Uruchamianie Osmos z Copilota wbudowanego w portal Fabric nie jest na razie obsługiwane. Zadanie startuje się z lokalnego agenta, np. GitHub Copilot CLI z zainstalowanym pakietem `fabric-skills@fabric-collection`.

## Co jest w Fabric

| Element | Wartość |
|---|---|
| Tenant | testowy tenant z capacity Fabric (`<tenant>`) |
| Capacity | `<capacity-name>`, F8, West Europe |
| Workspace | `Osmos-Demo` (`<workspace-id>`) |
| Lakehouse | `lh_retail` (`<lakehouse-id>`) |
| Dane surowe | `Files/raw/retail/` |

Zawartość `Files/raw/retail/` po wgraniu (sprawdzona listingiem OneLake DFS):

| Plik | Wiersze | Rozmiar | Uwagi |
|---|---|---|---|
| `stores.csv` | 12 | 533 B | 11 sklepów stacjonarnych i 1 kanał online |
| `customers.csv` | 2 040 | 154 491 B | separator przecinek |
| `products.csv` | 300 | 13 774 B | separator średnik |
| `orders/orders_part1.csv` | 25 125 | 1 543 026 B | zamówienia z okresu 1.11.2024 do 31.10.2026 |
| `orders/orders_part2.csv` | 25 125 | 1 543 046 B | druga część tego samego eksportu |

Wszystkie dane są syntetyczne, wygenerowane skryptem ze stałym ziarnem losowania. Nie ma w nich danych żadnego klienta.

## Wstrzyknięte problemy jakości

Skrypt policzył każdy problem, który dodał. Te liczby pozwalają po zakończeniu zadania sprawdzić, czy Osmos wychwycił wszystko, a nie tylko uwierzyć mu na słowo.

| Problem | Liczba |
|---|---|
| customers: zduplikowany wiersz | 40 |
| customers: puste miasto | 40 |
| customers: e-mail wielkimi literami | 38 |
| customers: segment małymi literami lub ze spacją na końcu | 78 |
| products: cena z przecinkiem dziesiętnym | 17 |
| orders: zduplikowane zamówienie (identyczny wiersz) | 250 |
| orders: data w formacie DD.MM.RRRR zamiast ISO | 2 042 |
| orders: brak customer_id | 532 |
| orders: customer_id spoza słownika klientów | 242 |
| orders: ujemna ilość | 521 |

Źródło: `dane/wstrzykniete_problemy.csv`. Kilka problemów może trafić na ten sam wiersz (np. zduplikowane zamówienie z datą w formacie polskim), więc sum nie należy porównywać jeden do jednego z liczbą odrzuconych rekordów.

Do tego produkty mają różny separator niż reszta plików, a zamówienia są rozbite na dwa pliki. Agent musi to zauważyć sam, bo prompt o tym nie wspomina.

## Prompt do uruchomienia

Treść jest też w pliku `prompt_osmos.txt`. Celowo opisuje wynik, a nie sposób jego osiągnięcia.

```text
W Lakehouse lh_retail w katalogu Files/raw/retail leżą surowe eksporty CSV
z sieci sklepów: customers.csv, products.csv, stores.csv oraz zamówienia
w katalogu orders/. Zbuduj z nich architekturę medalionową.

Bronze: wczytaj pliki bez zmian treści do tabel Delta bronze_customers,
bronze_products, bronze_stores i bronze_orders, dodając kolumny z nazwą pliku
źródłowego i czasem załadunku.

Silver: oczyść i ujednolić dane. Usuń duplikaty, ujednolić formaty dat,
liczb, e-maili i nazw segmentów, nadaj poprawne typy. Rekordy, których nie da
się naprawić (np. zamówienia bez klienta, z nieznanym klientem albo z ujemną
ilością), odłóż do tabeli silver_rejected_orders z kolumną opisującą powód
odrzucenia, zamiast je po cichu kasować.

Gold: utwórz gold_monthly_sales (miesiąc, kategoria produktu, segment klienta,
miasto sklepu, kanał, liczba zamówień, ilość, przychód netto po rabacie,
tylko status completed) oraz gold_customer_360 (klient, segment, pierwsze
i ostatnie zamówienie, liczba zamówień, przychód netto, udział zwrotów).

Dla każdej warstwy przygotuj osobny, przetestowany notebook zapisany
w workspace, tak aby całość można było uruchomić ponownie bez dublowania
danych. Na końcu podaj liczbę wierszy w każdej tabeli, liczbę odrzuconych
zamówień w podziale na powód i liczbę naprawionych rekordów w podziale na
typ problemu.
```

## Jak przeprowadzić demo

1. W GitHub Copilot CLI zalogowanym (`az login`) do swojego tenanta napisz: „Użyj Project Osmos z promptem z pliku prompt_osmos.txt na workspace Osmos-Demo i Lakehouse lh_retail”.
2. Skill przeprowadzi krótki wywiad o ustawieniach zadania: co agent może zmieniać, jak ma się zachować przy ponownym uruchomieniu, czy może zmieniać schematy, jaki ma być poziom rozumowania. Dla tego demo rozsądne jest pozwolenie na tworzenie nowych tabel i notebooków w `Osmos-Demo` bez prawa do zmian w innych workspace'ach.
3. Po starcie CLI wypisze kartę zadania z linkiem do strony zadania w portalu Fabric. Tę stronę warto pokazać na ekranie, bo widać na niej kolejne kroki agenta, kod i wyniki zapytań.
4. Postęp można sprawdzać w CLI pytaniem o status zadania. Jeśli Osmos zada pytanie, odpowiedź wraca do tego samego zadania. Nie tworzy się nowego.
5. Po zakończeniu w workspace powinny pojawić się notebooki i tabele `bronze_*`, `silver_*`, `gold_*`. Wyniki porównaj z tabelą wstrzykniętych problemów powyżej.

Czas trwania zadania i zużycie capacity F8 nie zostały zmierzone, bo zadanie nie było jeszcze uruchamiane. Przed prezentacją dla klienta warto zrobić jeden przebieg próbny.

## Co warto pokazać widowni

Najciekawsze są momenty, w których agent trafia na problem nieopisany w prompcie: średnik w `products.csv`, dwa formaty dat albo klientów, których nie ma w słowniku. Dobrze jest zapytać widownię, jak by to rozwiązali, a potem pokazać, co zrobił Osmos.

Drugi mocny punkt to rozliczalność. Liczby w raporcie końcowym da się porównać z `wstrzykniete_problemy.csv`. Jeśli coś się nie zgadza, jest to dobry pretekst do rozmowy o tym, że wynik agenta trzeba sprawdzać tak samo jak wynik pracy człowieka.

## Odtworzenie środowiska

Skrypty są w `metodyka/`.

```powershell
cd metodyka
python generuj_dane.py          # dane do ..\dane\raw, stały seed
.\przygotuj_workspace.ps1 -CapacityName <capacity-name>   # workspace, lakehouse, upload do OneLake
```

Skrypt `przygotuj_workspace.ps1` jest idempotentny w zakresie workspace i Lakehouse: jeśli już istnieją, użyje istniejących. Pliki nadpisze. Parametry `-WorkspaceName`, `-CapacityName` i `-LakehouseName` pozwalają postawić kopię w innym miejscu.

Identyfikator workspace wypisuje na końcu `przygotuj_workspace.ps1`. Workspace usuniesz poleceniem:

```powershell
az rest --method delete --url https://api.fabric.microsoft.com/v1/workspaces/<workspace-id> --resource https://api.fabric.microsoft.com
```

## Czego nie wiemy

- Nie sprawdzałem, czy Project Osmos jest włączony w tenancie testowym. Wyjdzie to dopiero przy pierwszej próbie utworzenia zadania.
- Nie wiadomo, ile potrwa zadanie i ile CU zużyje na F8.
- Nazwy notebooków i ich podział nadaje agent. Prompt prosi o jeden notebook na warstwę, ale ostateczny kształt zależy od Osmos.
- Opis możliwości Osmos pochodzi z dokumentacji skilla, a nie z Microsoft Learn. Przed pokazem klientowi warto sprawdzić aktualny status produktu (preview, dostępność regionalna).
