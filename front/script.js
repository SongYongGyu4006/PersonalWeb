const chatHistory = document.getElementById('chatHistory');
const promptInput = document.getElementById('promptInput');
const sendButton = document.getElementById('sendButton');

// ⚠️ 여기에 본인의 EC2 공인 IP를 넣으세요!
const BACKEND_URL = 'http://3.39.248.139:8000/chat';

let history = []; // 대화 문맥 저장
let userIP = 'unknown';

async function getMyIP() {
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        return data.ip;
    } catch (error) {
        console.error("IP 로드 실패:", error);
        return "unknown_user";
    }
}

async function sendMessage() {
    const text = promptInput.value.trim();
    userIP = await getMyIP(); 
    if (!text || userIP === "unknown") {
        userIP = await getMyIP();
        return;}
    // 1. 화면에 사용자 메시지 추가
    addMessage(text, 'user');
    promptInput.value = '';

    try {
        // 2. 백엔드(FastAPI)에 요청 보내기
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: text,
                history: history,
                user_ip: userIP
            })
        });

        const data = await response.json();
        
        // 3. 답변을 화면에 추가 및 히스토리 업데이트
        addMessage(data.answer, 'bot');
        history.push({ role: 'user', content: text });
        history.push({ role: 'assistant', content: data.answer });

    } catch (error) {
        console.error('Error:', error);
        addMessage('에러가 발생했습니다. 서버 연결을 확인해주세요.', 'bot');
    }
}

function addMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}-message`;
    
    if (role === 'bot') {
        // 마크다운을 해석하여 HTML로 넣어줍니다.
        div.innerHTML = marked.parse(text);
    } else {
        div.innerText = text;
    }
    
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

sendButton.addEventListener('click', sendMessage);
promptInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
// textarea 높이 자동 조절 로직
promptInput.addEventListener('input', () => {
    promptInput.style.height = 'auto';
    promptInput.style.height = promptInput.scrollHeight + 'px';
});


// 페이지가 로드되면 실행
window.onload = async () => {
    try {
        userIP = await getMyIP();
        console.log("접속 IP:", userIP);
        // 1. 백엔드에 유저IP 대화방의 히스토리를 요청
        const response = await fetch(`${BACKEND_URL.replace('/chat', '')}/history/${userIP}`);
        const data = await response.json();
        
        if (data.history) {
            // 2. 가져온 대화 내역을 화면에 하나씩 그림
            data.history.forEach(msg => {
                addMessage(msg.content, msg.role === 'user' ? 'user' : 'bot');
                
                // 3. 브라우저 메모리(history 변수)에도 동기화하여 문맥 유지
                history.push({ role: msg.role, content: msg.content });
            });
        }
    } catch (error) {
        console.error('기존 대화를 불러오는데 실패했습니다:', error);
    }
};