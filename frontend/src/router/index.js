import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import TestPage from '../views/TestPage.vue'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import RoomList from '../views/RoomList.vue'
import RoomDetail from '../views/RoomDetail.vue'
import UserManagement from '../views/UserManagement.vue'
import AdminSummary from '../views/AdminSummary.vue'
import AmbassadorDashboard from '../views/AmbassadorDashboard.vue'
import EngineerDashboard from '../views/EngineerDashboard.vue'

console.log('✅ Router loading...')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    children: [
      {
        path: '/rooms',
        name: 'RoomList',
        component: RoomList
      },
      {
        path: '/rooms/:id',
        name: 'RoomDetail',
        component: RoomDetail
      },
      {
        path: '/admin/users',
        name: 'UserManagement',
        component: UserManagement
      },
      {
        path: '/admin/summary',
        name: 'AdminSummary',
        component: AdminSummary
      },
      {
        path: '/ambassador',
        name: 'AmbassadorDashboard',
        component: AmbassadorDashboard
      },
      {
        path: '/engineer',
        name: 'EngineerDashboard',
        component: EngineerDashboard
      }
    ]
  },
  {
    path: '/test',
    name: 'Test',
    component: TestPage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

console.log('✅ Router configured with', routes.length, 'routes')

export default router