export const apiRoutes = {
  auth: {
    register: '/auth/register',
    login: '/auth/login',
    refresh: '/auth/refresh',
    logout: '/auth/logout',
  },
  players: {
    me: '/players/me',
    password: '/players/me/password',
  },
  world: {
    root: '/world',
    chunks: '/world/chunks',
    viewport: '/world/viewport',
    chopForest: '/world/tiles/chop-forest',
  },
  buildings: {
    catalog: '/buildings/catalog',
    list: '/buildings',
    detail: (id: string) => `/buildings/${id}`,
  },
  economy: {
    inventory: '/economy/inventory',
    transactions: '/economy/transactions',
    population: '/economy/population',
  },
  alliances: {
    me: '/alliances/me',
    create: '/alliances',
    invites: '/alliances/invites',
    invite: (id: string) => `/alliances/invites/${id}`,
    roles: '/alliances/roles',
    donations: '/alliances/treasury/donations',
    buffs: '/alliances/buffs',
    territoryAid: '/alliances/territory-aid',
  },
  chat: {
    messages: '/chat/messages',
  },
  market: {
    orders: '/market/orders',
    order: (id: string) => `/market/orders/${id}`,
  },
} as const
