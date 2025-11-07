import axios from 'axios';

const fallbackHost =
  typeof window !== 'undefined' && window.location.hostname
    ? window.location.hostname
    : 'localhost';
const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || `http://${fallbackHost}:8001/api`;

const client = axios.create({
  baseURL: API_BASE_URL,
});

export const getProjects = async () => {
  const { data } = await client.get('/projects');
  return data;
};

export const getProjectScenarios = async (projectId) => {
  const { data } = await client.get(`/projects/${projectId}/scenarios`);
  return data;
};

export const getScenarioTimeseries = async (projectId, scenarioId, params) => {
  const { data } = await client.get(
    `/projects/${projectId}/scenarios/${scenarioId}/timeseries`,
    { params }
  );
  return data;
};
