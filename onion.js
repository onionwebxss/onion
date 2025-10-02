document.addEventListener('DOMContentLoaded', function() {
    const text = "accessing hidden servers...";
    const typedTextElement = document.getElementById('typed-text');
    let index = 0;
    
    function typeWriter() {
        if (index < text.length) {
            typedTextElement.innerHTML += text.charAt(index);
            index++;
            setTimeout(typeWriter, 100);
        }
    }
    
    setTimeout(typeWriter, 1000);
    
    const terminal = document.querySelector('.terminal-body');
    setInterval(() => {
        const lines = [
            `[${new Date().toLocaleTimeString()}] Encrypted packet transmitted`,
            `[${new Date().toLocaleTimeString()}] Secure handshake completed`,
            `[${new Date().toLocaleTimeString()}] Data stream active`,
            `[${new Date().toLocaleTimeString()}] Connection stable`
        ];
        
        if (Math.random() > 0.7) {
            const line = document.createElement('div');
            line.className = 'line';
            line.innerHTML = lines[Math.floor(Math.random() * lines.length)];
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        }
    }, 3000);
    
    document.addEventListener('mousemove', function(e) {
        const particles = document.querySelector('.particles');
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = e.pageX + 'px';
        particle.style.top = e.pageY + 'px';
        particles.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 2000);
    });
});