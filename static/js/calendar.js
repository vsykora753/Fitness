document.addEventListener('DOMContentLoaded', function() {
    let currentDate = new Date(lessonsData.year, lessonsData.month - 1, 1);
    let selectedPopup = null;

    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const currentMonthElement = document.getElementById('currentMonth');
    const calendarDays = document.getElementById('calendar-days');

    // Názvy měsíců v češtině
    const months = [
        'Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
        'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'
    ];

    function updateCalendar() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        
        // Aktualizace názvu měsíce
        currentMonthElement.textContent = `${months[month]} ${year}`;

        // Vyčištění kalendáře
        calendarDays.innerHTML = '';

        // První den měsíce
        const firstDay = new Date(year, month, 1);
        // Poslední den měsíce
        const lastDay = new Date(year, month + 1, 0);
        
        // Začínáme od pondělí (1) místo neděle (0)
        let startDay = firstDay.getDay() - 1;
        if (startDay === -1) startDay = 6;

        // Přidání dnů z předchozího měsíce
        const prevMonthDays = startDay;
        const prevMonth = new Date(year, month, 0);
        for (let i = prevMonthDays - 1; i >= 0; i--) {
            addDayToCalendar(prevMonth.getDate() - i, true);
        }

        // Přidání dnů aktuálního měsíce
        for (let day = 1; day <= lastDay.getDate(); day++) {
            addDayToCalendar(day, false);
        }

        // Přidání dnů následujícího měsíce
        const remainingDays = 42 - (prevMonthDays + lastDay.getDate());
        for (let day = 1; day <= remainingDays; day++) {
            addDayToCalendar(day, true);
        }
    }

    function addDayToCalendar(day, isOtherMonth) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day' + (isOtherMonth ? ' other-month' : '');
        
        // Přidání čísla dne
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day;
        dayElement.appendChild(dayNumber);

        // Přidání lekcí pro tento den
        if (!isOtherMonth && lessonsData.lessons[day]) {
            const lessons = lessonsData.lessons[day];
            dayElement.classList.add('has-lessons');

            // Přidání teček pro indikaci lekcí
            const dotsContainer = document.createElement('div');
            dotsContainer.className = 'lesson-dots';
            for (let i = 0; i < Math.min(lessons.length, 3); i++) {
                const dot = document.createElement('div');
                dot.className = 'lesson-dot';
                dotsContainer.appendChild(dot);
            }
            dayElement.appendChild(dotsContainer);

            // Přidání náhledu první lekce
            if (lessons.length > 0) {
                const preview = document.createElement('div');
                preview.className = 'lesson-preview';
                preview.textContent = `${lessons[0].time} - ${lessons[0].title}`;
                dayElement.appendChild(preview);
            }

            // Přidání popup s lekcemi
            dayElement.addEventListener('click', (e) => {
                e.stopPropagation();
                showLessonsPopup(dayElement, lessons);
            });
        }

        // Kontrola, zda je den dnešní
        const today = new Date();
        if (!isOtherMonth && 
            day === today.getDate() && 
            currentDate.getMonth() === today.getMonth() && 
            currentDate.getFullYear() === today.getFullYear()) {
            dayElement.classList.add('today');
        }

        calendarDays.appendChild(dayElement);
    }

    function showLessonsPopup(dayElement, lessons) {
        // Zavření předchozího popupu
        if (selectedPopup) {
            selectedPopup.remove();
        }

        // Vytvoření nového popupu
        const popupTemplate = document.getElementById('lessons-popup-template');
        const popup = popupTemplate.content.cloneNode(true);
        const popupContainer = popup.querySelector('.lessons-popup');

        // Přidání lekcí do popupu
        lessons.forEach(lesson => {
            const lessonItem = document.createElement('div');
            lessonItem.className = 'lesson-item';
            lessonItem.innerHTML = `
                <div class="lesson-time">${lesson.time}</div>
                <div class="lesson-title">${lesson.title}</div>
                <div class="lesson-instructor">${lesson.instructor}</div>
                <div class="lesson-spots">Volná místa: ${lesson.available_spots}</div>
                <a href="/lesson/${lesson.id}/" class="btn">Rezervovat</a>
            `;
            popupContainer.appendChild(lessonItem);
        });

        // Umístění popupu
        dayElement.appendChild(popupContainer);
        selectedPopup = popupContainer;

        // Zavření popupu při kliknutí mimo
        document.addEventListener('click', function closePopup(e) {
            if (!popupContainer.contains(e.target) && !dayElement.contains(e.target)) {
                popupContainer.remove();
                selectedPopup = null;
                document.removeEventListener('click', closePopup);
            }
        });
    }

    // Ovládání kalendáře
    prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        // Zde by se měly načíst nová data pro předchozí měsíc z backendu
        updateCalendar();
    });

    nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        // Zde by se měly načíst nová data pro následující měsíc z backendu
        updateCalendar();
    });

    // Inicializace kalendáře
    updateCalendar();
});