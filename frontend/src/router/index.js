import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '../auth'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../views/MainLayout.vue'
import ScanView from '../views/ScanView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView,
          meta: { title: 'IP 管理' },
        },
        {
          path: 'scan',
          name: 'scan',
          component: ScanView,
          meta: { title: '检测工具' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) {
    if (to.name === 'login' && isLoggedIn()) {
      return { name: 'home' }
    }
    return true
  }
  if (!isLoggedIn()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
