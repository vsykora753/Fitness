document.addEventListener('DOMContentLoaded', function() {
    let currentDate = new Date(lessonsData.year, lessonsData.month - 1, 1);
    let selectedPopup = null;

    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const currentMonthElement = document.getElementById('currentMonth');
    const calendarDays = document.getElementById('calendar-days');

    const months = [
        'Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
        'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'
    ];

    let activeCategory = 'all';

    function updateCalendar() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        currentMonthElement.textContent = `${months[month]} ${year}`;
        calendarDays.innerHTML = '';

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);

        // JavaScript: 0=neděle, 1=pondělí, ..., 6=sobota
        // Kalendář: Po=0, Út=1, ..., Ne=6
        // Převod: (jsDay + 6) % 7
        let startDay = (firstDay.getDay() + 6) % 7;

        const prevMonthDays = startDay;
        const prevMonth = new Date(year, month, 0);

        // První týden - dny z předchozího měsíce
        for (let i = prevMonthDays - 1; i >= 0; i--) {
            addDayToCalendar(prevMonth.getDate() - i, true);
        }

        // Dny aktuálního měsíce
        for (let day = 1; day <= lastDay.getDate(); day++) {
            addDayToCalendar(day, false);
        }

        // Dny následujícího měsíce
        const remainingDays = 42 - (prevMonthDays + lastDay.getDate());
        for (let day = 1; day <= remainingDays; day++) {
            addDayToCalendar(day, true);
        }
    }

    function addDayToCalendar(day, isOtherMonth) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day' + (isOtherMonth ? ' other-month' : '');

        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day;
        dayElement.appendChild(dayNumber);

        if (!isOtherMonth) {
            // Sestavíme YYYY-MM-DD pro aktuální den
            const year = currentDate.getFullYear();
            const month = (currentDate.getMonth() + 1).toString().padStart(2, '0');
            const dayStr = day.toString().padStart(2, '0');
            const dateKey = `${year}-${month}-${dayStr}`;
            const lessons = getLessonsForDay(dateKey);
            if (lessons && lessons.length > 0) {
                dayElement.classList.add('has-lessons');

                const dotsContainer = document.createElement('div');
                dotsContainer.className = 'lesson-dots';
                for (let i = 0; i < Math.min(lessons.length, 3); i++) {
                    const dot = document.createElement('div');
                    dot.className = 'lesson-dot';
                    dotsContainer.appendChild(dot);
                }
                dayElement.appendChild(dotsContainer);

                // Zobrazení lekcí přímo v buňce
                const lessonsPreview = document.createElement('div');
                lessonsPreview.className = 'lessons-preview';

                lessons.forEach(lesson => {
                    const item = document.createElement('div');
                    item.className = 'lesson-preview-item';
                    item.textContent = `${lesson.time} - ${lesson.title} (${lesson.available_spots}/${lesson.capacity})`;

                    item.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const detailUrl = lessonDetailBase.replace(/0\/$/, `${lesson.id}/`);
                        window.location.href = detailUrl;
                    });

                    lessonsPreview.appendChild(item);
                });

                dayElement.appendChild(lessonsPreview);

                dayElement.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('lesson-preview-item')) {
                        showLessonsPopup(dayElement, lessons);
                    }
                });
            }
        }

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
        if (selectedPopup) selectedPopup.remove();

        const popupTemplate = document.getElementById('lessons-popup-template');
        const popup = popupTemplate.content.cloneNode(true);
        const popupContainer = popup.querySelector('.lessons-popup');

        lessons.forEach(lesson => {
            const lessonItem = document.createElement('div');
            lessonItem.className = 'lesson-item';
            const detailUrl = lessonDetailBase.replace(/0\/$/, `${lesson.id}/`);

            lessonItem.innerHTML = `
                <div class="lesson-time">${lesson.time}</div>
                <div class="lesson-title">${lesson.title}</div>
                <div class="lesson-location">Místo: ${lesson.location}</div>
                <div class="lesson-instructor">Lektor: ${lesson.instructor}</div>
                <div class="lesson-duration">Délka: ${lesson.duration} minut</div>
                <div class="lesson-spots">Volná místa: ${lesson.available_spots}/${lesson.capacity}</div>
                <div class="lesson-price">Cena: ${lesson.price} Kč</div>
                <a href="${detailUrl}" class="btn">Rezervovat</a>
            `;
            popupContainer.appendChild(lessonItem);
        });

        dayElement.appendChild(popupContainer);
        selectedPopup = popupContainer;

        document.addEventListener('click', function closePopup(e) {
            if (!popupContainer.contains(e.target) && !dayElement.contains(e.target)) {
                popupContainer.remove();
                selectedPopup = null;
                document.removeEventListener('click', closePopup);
            }
        });
    }

    function getLessonsForDay(day) {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        const monthKey = `${year}-${month}`;
        const monthData = lessonsData.allMonths[monthKey] || {};
        const all = monthData[day] || [];
        
        if (activeCategory === 'all') return all;
        return all.filter(l => l.category === activeCategory);
    }

    const categoryTabs = document.querySelectorAll('.category-tab');
    categoryTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            categoryTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeCategory = tab.dataset.category || 'all';
            updateCalendar();
        });
    });

    prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        updateCalendar();
    });

    nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        updateCalendar();
    });

    updateCalendar();
});
