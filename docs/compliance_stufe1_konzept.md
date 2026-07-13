# Compliance Stufe 1 – Konzept der regelbasierten PII- und Sensibilitätsprüfung

Stand: 2026-07-13, Branch `feature/compliance-stufe1`.
Betroffener Code: `app/services/compliance_service.py`, Tests in `tests/test_compliance_stufe1.py`.

Stufe 1 ist eine rein regelbasierte, lokal laufende Vorprüfung jedes Prompts, bevor er an ein
Modell geht. Sie ist bewusst konservativ gebaut: Muster finden Kandidaten, Prüfsummen bzw.
Strukturregeln bestätigen sie. Jeder bestätigte Treffer erscheint als benannter Flag in
`findings` und ist damit im UI erklärbar.

## 1. Erkannte Datenarten

| Flag | Validierung | Einordnung DSGVO | Einordnung KDG |
|---|---|---|---|
| E-Mail-Adresse | Muster | Personenbezogenes Datum, Art. 4 Nr. 1 | § 4 Nr. 1 |
| Telefonnummer | Muster (+49-/0xxx-Formate, 7–11 Ziffern national) | Personenbezogenes Datum, Art. 4 Nr. 1 | § 4 Nr. 1 |
| IBAN | Mod-97-Prüfsumme und Länderlänge (ISO 13616), Prüfziffern 02–98; DE zusätzlich: numerische BBAN | Personenbezogenes Datum mit Finanzbezug, Art. 4 Nr. 1 | § 4 Nr. 1 |
| Kreditkartennummer | Luhn-Prüfsumme, 13–19 Ziffern, keine führende Null | Personenbezogenes Datum mit Finanzbezug, Art. 4 Nr. 1 | § 4 Nr. 1 |
| Deutsche Steuer-ID | Strukturregel + Prüfziffer (ISO 7064, MOD 11,10) | Nationale Kennziffer (§ 139b AO), Art. 87 | § 4 Nr. 1 |
| Gesundheitsdaten | Schlagwortliste | Besondere Kategorie, Art. 9 | § 4 Nr. 2, § 11 |
| Finanzdaten | Schlagwortliste | Personenbezogenes Datum, Art. 4 Nr. 1 | § 4 Nr. 1 |
| Vertrauliche Informationen | Schlagwortliste | Geschäftsgeheimnis (GeschGehG), kein PII i. e. S. | – |
| API-Schlüssel / Bearer-Token / Privater Schlüssel / Passwort | Muster | Sicherheit der Verarbeitung, Art. 32 | § 26 |
| Schädliche oder rechtswidrige Anfrage | Schlagwortliste | – (Missbrauchsprävention) | – |
| Urheberrechtsrisiko | Schlagwortliste | – (UrhG) | – |
| Geheimnis im Klartext | Schlagwortliste | Sicherheit der Verarbeitung, Art. 32 | § 26 |

Kernprinzip der neuen Erkennung: **Kandidat per Regex, Bestätigung per Prüfsumme.** Eine
16-stellige Zahl ohne gültige Luhn-Prüfsumme, eine DE-Zeichenfolge ohne gültige
Mod-97-Prüfsumme oder eine beliebige 11-stellige Zahl ohne gültige Steuer-ID-Prüfziffer
lösen keinen Flag mehr aus. Telefonmuster sind auf deutschlandtypische Formate begrenzt
(+49-Formate inkl. „+49 (0) 30 …", 0xxx-Formate, Klammer-Vorwahl „(030) …", Trenner
Leerzeichen/-//), sodass Jahreszahlen, Postleitzahlen (auch 0xxxx), Preise (1.250,50 €),
Datumsangaben (01/02/2023, 07/2019-06/2023) und gleichförmig segmentierte Kennungen
(0815-4711-2026) nicht anschlagen. Erkannte Nummern dürfen in 4er-Gruppen mit
Leerzeichen, geschütztem Leerzeichen (Word/PDF-Kopien) oder Bindestrich geschrieben
sein; einer Kreditkarte folgende Ablaufdaten/CVV stören die Erkennung nicht.
Es gilt eine Vorrangregel: Ziffern innerhalb einer bestätigten IBAN oder Kreditkarte
werden nicht zusätzlich als Telefonnummer oder Steuer-ID gewertet.

## 2. Bewertung: Punkte, Deckel, Ampel

- Jeder Prompt startet mit **100 Punkten**; pro gefundener Kategorie werden Strafpunkte
  abgezogen (Muster-Kategorien je 18, Schlagwort-Kategorien 12–35 je nach Schwere).
- **Deckel pro Kategorie:** Jede Kategorie zählt höchstens einmal, egal wie viele Treffer
  der Text enthält. Zehn E-Mail-Adressen wiegen nicht schwerer als eine.
- **Deckel für schwache Treffer:** Die heuristischen Kategorien Telefonnummer,
  Urheberrechtsrisiko und Geheimnis im Klartext tragen zusammen höchstens **35 Punkte**
  bei. Damit können viele unsichere Signale allein nie eine rote Bewertung erzwingen
  (Score-Untergrenze 65 bei ausschließlich schwachen Treffern).
- Der Gesamtabzug ist auf 100 begrenzt; der Score bleibt im Bereich 0–100.
- **Ampel-Schwellen unverändert:** ≥ 80 grün, ≥ 50 gelb, darunter rot.

Wirkung im System (`app/routes/api.py`): Eine rote Bewertung blockiert `/api/send`, sofern
keine manuelle Freigabe mit Begründung erfolgt; der Compliance-Score wird außerdem per
`min()` mit dem Score der LLM-Analyse verrechnet, kann diesen also nur verschärfen, nie
aufweichen.

## 3. Bewusste Grenzen der Stufe 1 (Ausblick Stufe 2)

- **Namen, Adressen, Geburtsdaten** in Freitext werden nicht erkannt – dafür braucht es
  NER bzw. ein Guard-Modell, nicht Regeln. Geplant für Stufe 2 mit granite-guardian.
- **Gesundheits- und Religionsdaten in Freitext** werden nur über eine enge Schlagwortliste
  angerissen. Formulierungen ohne Signalwort („er kommt seit dem Unfall nicht zur Arbeit")
  bleiben unerkannt. Gerade die im KDG-Kontext zentrale Religionszugehörigkeit (§ 11 KDG)
  ist regelbasiert kaum greifbar → Stufe 2.
- **Kontext wird nicht bewertet:** Eine prüfsummen-gültige Nummer in offensichtlich
  harmlosem Kontext (z. B. dokumentierte Testwerte) wird trotzdem geflaggt; umgekehrt gibt
  es ein statistisches Restrisiko (~10 % zufällig Luhn-gültige Zahlenfolgen).
- **Schreibweisen:** Die Steuer-ID wird nur zusammenhängend 11-stellig erkannt (nicht
  in der BZSt-Gruppierung „86 095 742 719"), Telefonnummern nur für Deutschland (+49/0…,
  keine internationalen Formate wie +43 oder +1 – dadurch kippt bei ausländischen Nummern
  auch `contains_personal_data` nicht mehr auf True), IBANs nur für die im Code
  hinterlegten EU-/EWR-Länder. Über Zeilenumbrüche verteilte oder mit Punkten gruppierte
  Nummern sowie Nicht-ASCII-Ziffern (z. B. ٨٦٠…) werden nicht erkannt.
- **Keine Verschleierungserkennung:** Absichtlich verfremdete Angaben (Leetspeak,
  „vier-eins-eins-eins…") liegen außerhalb des Regelansatzes.
- **Vorbestehende Unschärfen (nicht Teil dieser Änderung):** Die unverändert
  übernommenen Muster und Schlagwörter erzeugen bekannte Fehlalarme in deutschem
  IT-Geschäftstext: Komposita wie „API-Schnittstelle" treffen das API-Schlüssel-Muster,
  generische Sätze wie „Das Passwort ist regelmäßig zu ändern" das Passwort-Muster, das
  Idiom „Im Klartext: …" das Klartext-Schlagwort und „Diagnose" im Technik-Kontext das
  Gesundheitsdaten-Schlagwort. In Kombination kann harmloser Text so Rot erreichen und
  den Versand blockieren. Diese Muster anzufassen war bewusst nicht Teil von Stufe 1;
  sie gehören in die Kalibrierungsrunde (Frage 2).

## 4. Offene Entscheidungsfragen fürs Team

1. **Einsatz von `redact_sensitive` – ja/nein und wo?** Die Funktion maskiert validierte
   Treffer (z. B. `411***1111`). Optionen: (a) automatisch vor jedem Versand an externe
   Provider, (b) nur bei gelber Bewertung als Angebot im UI, (c) gar nicht, nur Anzeige.
   Abwägung: Datenminimierung (Art. 5 Abs. 1 lit. c DSGVO / § 7 Abs. 1 lit. c KDG) gegen
   verfälschte Prompts und damit schlechtere Antworten.
2. **Kalibrierung der Schwellenwerte:** Punktehöhen (12–35), der Deckel für schwache
   Treffer (35) und die Ampel-Schwellen (80/50) sind gesetzte Startwerte. Sie sollten
   gegen einen Korpus realer (anonymisierter) Prompts aus dem Alltag evaluiert werden –
   inklusive der Frage, wer die Zielwerte abnimmt (Datenschutzbeauftragte:r?). Zwei
   bekannte Diskussionspunkte: Ein einzelner validierter starker Fund (z. B. eine
   Kreditkarte) ergibt mit 18 Punkten noch Grün (82); und der Deckel kann Kombinationen
   aus mehreren schwachen Treffern plus einem kleinen starken Fund (Finanzdaten, 14) von
   vormals Rot auf Gelb heben – beides gewollt konservativ, aber abstimmungsbedürftig.
3. **Trigger-Kriterien für Stufe 2 (granite-guardian):** Läuft das Guard-Modell immer,
   nur bei gelber Bewertung, nur bei Versand an externe/nicht-EU-Provider oder ab einer
   bestimmten Promptlänge? Abwägung: Latenz und lokale Rechenlast gegen Abdeckung der
   oben genannten Lücken.
