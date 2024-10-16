import {
  IconBell,
  IconBook,
  IconCalendar,
  IconCheck,
  IconCloud,
  IconCpu,
  IconDatabase,
  IconDeviceDesktop,
  IconDeviceMobile,
  IconDisc,
  IconHeart,
  IconHome,
  IconLock,
  IconMessage,
  IconNetwork,
  IconQuestionMark,
  IconRouter,
  IconSearch,
  IconServer,
  IconSettings,
  IconStar,
  IconUsb,
  IconUser,
  IconWifi,
  IconX,
  type TablerIcon,
} from '@tabler/icons-react';
import { rem } from '@mantine/core';

export const UserDefinedIcon = ({ icon }: { icon: string }) => {
  const icon_lut = {
    lock: IconLock,
    user: IconUser,
    home: IconHome,
    settings: IconSettings,
    search: IconSearch,
    bell: IconBell,
    heart: IconHeart,
    star: IconStar,
    message: IconMessage,
    calendar: IconCalendar,
    check: IconCheck,
    x: IconX,
    server: IconServer,
    network: IconNetwork,
    database: IconDatabase,
    desktop: IconDeviceDesktop,
    mobile: IconDeviceMobile,
    cloud: IconCloud,
    cpu: IconCpu,
    disc: IconDisc,
    router: IconRouter,
    wifi: IconWifi,
    usb: IconUsb,
    question_mark: IconQuestionMark,
    book: IconBook,
  } as { [key: string]: TablerIcon };

  const Icon = icon_lut?.[icon] ?? IconLock;
  return <Icon style={{ width: rem(18), height: rem(18) }} />;
};

export default UserDefinedIcon;
