import { create } from 'zustand';
import dataService, { UserInfo } from '@/services/data.service';

interface UserInfoStore {
  load_user_info: () => Promise<void>;
  user_info: UserInfo | null;
}

export const useUserInfoStore = create<UserInfoStore>()((set) => ({
  user_info: null,
  load_user_info: async () => set({ user_info: await dataService.getUserInfo() }),
}));
