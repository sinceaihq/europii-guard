"""Message templates for the synthetic evaluation set.

Placeholders in braces are filled by :mod:`europii.bench.synthetic`. PII
slots: NAME, EMAIL, PHONE (national format), PHONE_INTL, IBAN, CARD, ID (the
local national identifier), VAT, IP. Hard-negative slots (never PII): ORDER,
INVOICE, DATE, AMOUNT, BAD_ID (local identifier layout with a failing
checksum), BAD_IBAN, EAN (product barcode), POSTCODE.
"""

from __future__ import annotations

TEMPLATES: dict[str, list[str]] = {
    "en": [
        "Hi, this is {NAME}. My order {ORDER} from {DATE} has not arrived. You can reach me on {PHONE} or at {EMAIL}.",
        "Employee record: {NAME}, PPS number {ID}, salary account {IBAN}. Contract start {DATE}, monthly gross {AMOUNT}.",
        "Refund request for invoice {INVOICE}: please return {AMOUNT} to card {CARD} (cardholder {NAME}).",
        "Login alert for {EMAIL}: new sign-in from {IP} on {DATE}. Reference {BAD_ID} was not recognised.",
        "Supplier {NAME} Ltd, VAT number {VAT}, phone {PHONE_INTL}. Item EAN {EAN}, postcode {POSTCODE}.",
    ],
    "fi": [
        "Hei, olen {NAME}. Tilaukseni {ORDER} ({DATE}) ei ole saapunut. Tavoitatte minut numerosta {PHONE} tai osoitteesta {EMAIL}.",
        "Työntekijä {NAME}, henkilötunnus {ID}, palkkatili {IBAN}. Työsuhde alkaa {DATE}, kuukausipalkka {AMOUNT}.",
        "Hyvitys laskusta {INVOICE}: palauttakaa {AMOUNT} kortille {CARD}, kortinhaltija {NAME}.",
        "Kirjautumisilmoitus tunnukselle {EMAIL}: uusi kirjautuminen osoitteesta {IP} {DATE}. Viitettä {BAD_ID} ei tunnistettu.",
        "Toimittaja {NAME} Oy, ALV-numero {VAT}, puh. {PHONE_INTL}. Tuotteen EAN {EAN}, postinumero {POSTCODE}.",
    ],
    "sv": [
        "Hej, jag heter {NAME}. Min beställning {ORDER} från {DATE} har inte kommit. Ni når mig på {PHONE} eller {EMAIL}.",
        "Anställd: {NAME}, personnummer {ID}, lönekonto {IBAN}. Anställningen börjar {DATE}, månadslön {AMOUNT}.",
        "Återbetalning för faktura {INVOICE}: betala tillbaka {AMOUNT} till kort {CARD} (kortinnehavare {NAME}).",
        "Inloggningsvarning för {EMAIL}: ny inloggning från {IP} den {DATE}. Referensen {BAD_ID} kändes inte igen.",
        "Leverantör {NAME} AB, momsreg.nr {VAT}, tel. {PHONE_INTL}. Artikelns EAN {EAN}, postnummer {POSTCODE}.",
    ],
    "de": [
        "Guten Tag, hier ist {NAME}. Meine Bestellung {ORDER} vom {DATE} ist nicht angekommen. Sie erreichen mich unter {PHONE} oder {EMAIL}.",
        "Personalakte: {NAME}, Steuer-ID {ID}, Gehaltskonto {IBAN}. Beginn am {DATE}, Bruttogehalt {AMOUNT}.",
        "Erstattung zur Rechnung {INVOICE}: bitte {AMOUNT} auf die Karte {CARD} zurückbuchen (Karteninhaber {NAME}).",
        "Anmeldehinweis für {EMAIL}: neue Anmeldung von {IP} am {DATE}. Die Referenz {BAD_ID} wurde nicht erkannt.",
        "Lieferant {NAME} GmbH, USt-IdNr. {VAT}, Tel. {PHONE_INTL}. Artikel-EAN {EAN}, PLZ {POSTCODE}.",
    ],
    "fr": [
        "Bonjour, je suis {NAME}. Ma commande {ORDER} du {DATE} n'est pas arrivée. Vous pouvez me joindre au {PHONE} ou à {EMAIL}.",
        "Dossier salarié : {NAME}, numéro de sécurité sociale {ID}, compte de paie {IBAN}. Début le {DATE}, salaire brut {AMOUNT}.",
        "Remboursement de la facture {INVOICE} : merci de recréditer {AMOUNT} sur la carte {CARD} (titulaire {NAME}).",
        "Alerte de connexion pour {EMAIL} : nouvelle connexion depuis {IP} le {DATE}. La référence {BAD_ID} est inconnue.",
        "Fournisseur {NAME} SAS, n° TVA {VAT}, tél. {PHONE_INTL}. EAN de l'article {EAN}, code postal {POSTCODE}.",
    ],
    "nl": [
        "Hallo, met {NAME}. Mijn bestelling {ORDER} van {DATE} is niet aangekomen. U kunt mij bereiken op {PHONE} of via {EMAIL}.",
        "Personeelsdossier: {NAME}, BSN {ID}, salarisrekening {IBAN}. Start op {DATE}, brutoloon {AMOUNT}.",
        "Terugbetaling voor factuur {INVOICE}: graag {AMOUNT} terugstorten op kaart {CARD} (kaarthouder {NAME}).",
        "Inlogmelding voor {EMAIL}: nieuwe aanmelding vanaf {IP} op {DATE}. Referentie {BAD_ID} is niet herkend.",
        "Leverancier {NAME} B.V., btw-nummer {VAT}, tel. {PHONE_INTL}. EAN van het artikel {EAN}, postcode {POSTCODE}.",
    ],
    "it": [
        "Buongiorno, sono {NAME}. Il mio ordine {ORDER} del {DATE} non è arrivato. Potete contattarmi al {PHONE} o a {EMAIL}.",
        "Scheda dipendente: {NAME}, codice fiscale {ID}, conto stipendio {IBAN}. Inizio il {DATE}, retribuzione lorda {AMOUNT}.",
        "Rimborso della fattura {INVOICE}: restituire {AMOUNT} sulla carta {CARD} (titolare {NAME}).",
        "Avviso di accesso per {EMAIL}: nuovo accesso da {IP} il {DATE}. Il riferimento {BAD_ID} non è stato riconosciuto.",
        "Fornitore {NAME} S.r.l., partita IVA {VAT}, tel. {PHONE_INTL}. EAN dell'articolo {EAN}, CAP {POSTCODE}.",
    ],
    "es": [
        "Hola, soy {NAME}. Mi pedido {ORDER} del {DATE} no ha llegado. Pueden contactarme en el {PHONE} o en {EMAIL}.",
        "Ficha de empleado: {NAME}, DNI {ID}, cuenta de nómina {IBAN}. Alta el {DATE}, salario bruto {AMOUNT}.",
        "Reembolso de la factura {INVOICE}: devuelvan {AMOUNT} a la tarjeta {CARD} (titular {NAME}).",
        "Aviso de inicio de sesión para {EMAIL}: nuevo acceso desde {IP} el {DATE}. La referencia {BAD_ID} no se reconoce.",
        "Proveedor {NAME} S.L., NIF-IVA {VAT}, tel. {PHONE_INTL}. EAN del artículo {EAN}, código postal {POSTCODE}.",
    ],
    "pl": [
        "Dzień dobry, nazywam się {NAME}. Moje zamówienie {ORDER} z {DATE} nie dotarło. Proszę o kontakt pod numerem {PHONE} lub {EMAIL}.",
        "Kartoteka pracownika: {NAME}, PESEL {ID}, konto do wypłat {IBAN}. Początek zatrudnienia {DATE}, wynagrodzenie brutto {AMOUNT}.",
        "Zwrot za fakturę {INVOICE}: proszę zwrócić {AMOUNT} na kartę {CARD} (posiadacz {NAME}).",
        "Powiadomienie o logowaniu dla {EMAIL}: nowe logowanie z {IP} dnia {DATE}. Nie rozpoznano numeru {BAD_ID}.",
        "Dostawca {NAME} Sp. z o.o., NIP UE {VAT}, tel. {PHONE_INTL}. Kod EAN produktu {EAN}, kod pocztowy {POSTCODE}.",
    ],
    "pt": [
        "Olá, sou {NAME}. A minha encomenda {ORDER} de {DATE} não chegou. Podem contactar-me pelo {PHONE} ou por {EMAIL}.",
        "Ficha do trabalhador: {NAME}, cartão de cidadão {ID}, conta para salário {IBAN}. Início a {DATE}, salário bruto {AMOUNT}.",
        "Reembolso da fatura {INVOICE}: devolvam {AMOUNT} ao cartão {CARD} (titular {NAME}).",
        "Alerta de início de sessão para {EMAIL}: novo acesso a partir de {IP} em {DATE}. A referência {BAD_ID} não foi reconhecida.",
        "Fornecedor {NAME} Lda., NIF-IVA {VAT}, tel. {PHONE_INTL}. EAN do artigo {EAN}, código postal {POSTCODE}.",
    ],
    "cs": [
        "Dobrý den, jmenuji se {NAME}. Moje objednávka {ORDER} z {DATE} nedorazila. Zastihnete mě na čísle {PHONE} nebo na {EMAIL}.",
        "Osobní karta: {NAME}, rodné číslo {ID}, mzdový účet {IBAN}. Nástup {DATE}, hrubá mzda {AMOUNT}.",
        "Vrácení platby za fakturu {INVOICE}: vraťte prosím {AMOUNT} na kartu {CARD} (držitel {NAME}).",
        "Upozornění na přihlášení pro {EMAIL}: nové přihlášení z {IP} dne {DATE}. Číslo {BAD_ID} nebylo rozpoznáno.",
        "Dodavatel {NAME} s.r.o., DIČ {VAT}, tel. {PHONE_INTL}. EAN zboží {EAN}, PSČ {POSTCODE}.",
    ],
    "da": [
        "Hej, det er {NAME}. Min ordre {ORDER} fra {DATE} er ikke kommet. I kan træffe mig på {PHONE} eller {EMAIL}.",
        "Medarbejder: {NAME}, CPR-nr. {ID}, lønkonto {IBAN}. Start den {DATE}, bruttoløn {AMOUNT}.",
        "Refusion af faktura {INVOICE}: tilbagebetal venligst {AMOUNT} til kort {CARD} (kortholder {NAME}).",
        "Login-advarsel for {EMAIL}: nyt login fra {IP} den {DATE}. Referencen {BAD_ID} blev ikke genkendt.",
        "Leverandør {NAME} ApS, momsnr. {VAT}, tlf. {PHONE_INTL}. Varens EAN {EAN}, postnummer {POSTCODE}.",
    ],
}  # fmt: skip

# English messages that mention identifiers from the remaining countries.
FOREIGN_TEMPLATES: dict[str, list[str]] = {
    "no_fodselsnummer": ["Passenger {NAME}, Norwegian national identity number {ID}, booking {ORDER}."],
    "be_national_number": ["Tenant {NAME}, Belgian national number {ID}, deposit {AMOUNT} paid on {DATE}."],
    "ee_isikukood": ["Applicant {NAME}, Estonian personal identification code {ID}, reference {INVOICE}."],
    "lt_asmens_kodas": ["Patient {NAME}, Lithuanian personal code {ID}, appointment on {DATE}."],
    "lv_personas_kods": ["Student {NAME}, Latvian personal code {ID}, enrolment number {ORDER}."],
    "sk_rodne_cislo": ["Driver {NAME}, Slovak personal identification number {ID}, permit {INVOICE}."],
    "si_emso": ["Member {NAME}, Slovenian personal number {ID}, membership since {DATE}."],
    "ro_cnp": ["Customer {NAME}, Romanian personal numeric code {ID}, contract {ORDER}."],
    "bg_egn": ["Guest {NAME}, Bulgarian personal number {ID}, room booked until {DATE}."],
    "hr_oib": ["Owner {NAME}, Croatian personal identification number {ID}, vehicle order {ORDER}."],
    "at_svnr": ["Employee {NAME}, Austrian social security number {ID}, start {DATE}."],
}  # fmt: skip

LOCAL_ID = {
    "en": ("ie_ppsn",),
    "fi": ("fi_hetu",),
    "sv": ("se_personnummer",),
    "de": ("de_steuer_id",),
    "fr": ("fr_nir",),
    "nl": ("nl_bsn",),
    "it": ("it_codice_fiscale",),
    "es": ("es_dni", "es_nie"),
    "pl": ("pl_pesel",),
    "pt": ("pt_cc",),
    "cs": ("cz_rodne_cislo",),
    "da": ("dk_cpr",),
}
COUNTRY = {"en": "IE", "fi": "FI", "sv": "SE", "de": "DE", "fr": "FR", "nl": "NL", "it": "IT",
           "es": "ES", "pl": "PL", "pt": "PT", "cs": "CZ", "da": "DK"}  # fmt: skip

FIRST_NAMES = {
    "en": ("Aoife", "Ciarán", "Siobhán", "Patrick", "Niamh", "Liam", "Emma", "Conor"),
    "fi": ("Aino", "Eetu", "Helmi", "Juho", "Kaisa", "Mikko", "Saara", "Ville"),
    "sv": ("Astrid", "Erik", "Ingrid", "Johan", "Karin", "Lars", "Maja", "Oskar"),
    "de": ("Anna", "Felix", "Greta", "Jonas", "Lena", "Lukas", "Marie", "Paul"),
    "fr": ("Camille", "Élodie", "Hugo", "Léa", "Louis", "Manon", "Théo", "Zoé"),
    "nl": ("Daan", "Emma", "Femke", "Joost", "Lotte", "Sem", "Sanne", "Thijs"),
    "it": ("Alessandro", "Chiara", "Francesca", "Giulia", "Lorenzo", "Marco", "Sofia", "Matteo"),
    "es": ("Alejandro", "Carmen", "Javier", "Lucía", "María", "Pablo", "Sofía", "Álvaro"),
    "pl": ("Agnieszka", "Bartosz", "Katarzyna", "Łukasz", "Magdalena", "Piotr", "Zofia", "Wojciech"),
    "pt": ("Beatriz", "Duarte", "Inês", "João", "Leonor", "Rodrigo", "Mariana", "Tiago"),
    "cs": ("Jana", "Jiří", "Kateřina", "Lukáš", "Petra", "Tomáš", "Tereza", "Ondřej"),
    "da": ("Freja", "Mads", "Ida", "Rasmus", "Sofie", "Mikkel", "Emma", "Frederik"),
}  # fmt: skip
LAST_NAMES = {
    "en": ("Murphy", "Kelly", "O'Sullivan", "Walsh", "Byrne", "Ryan", "O'Brien", "Doyle"),
    "fi": ("Korhonen", "Virtanen", "Mäkinen", "Nieminen", "Hämäläinen", "Laine", "Heikkinen", "Koskinen"),
    "sv": ("Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson"),
    "de": ("Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker"),
    "fr": ("Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand"),
    "nl": ("de Jong", "Jansen", "de Vries", "van den Berg", "Bakker", "Visser", "Smit", "Meijer"),
    "it": ("Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci"),
    "es": ("García", "Fernández", "González", "Rodríguez", "López", "Martínez", "Sánchez", "Pérez"),
    "pl": ("Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński"),
    "pt": ("Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues", "Martins"),
    "cs": ("Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Kučera", "Veselý"),
    "da": ("Nielsen", "Jensen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen", "Sørensen"),
}  # fmt: skip
