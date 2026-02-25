import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
    timeout: 120000,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle global errors here (e.g., logging, toast notifications)
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export default api;
