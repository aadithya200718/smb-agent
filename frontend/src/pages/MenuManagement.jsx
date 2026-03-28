import { useState } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Input from '../components/common/Input';
import Modal from '../components/common/Modal';
import { Edit2, Trash2, Plus, Languages } from 'lucide-react';

export default function MenuManagement() {
  const [items, setItems] = useState([
    { id: '1', name: 'Butter Chicken', hindi_name: 'बटर चिकन', price: 350, category: 'Main Course', available: true },
    { id: '2', name: 'Garlic Naan', hindi_name: 'लहसुन नान', price: 60, category: 'Breads', available: true },
    { id: '3', name: 'Paneer Tikka', hindi_name: 'पनीर टिक्का', price: 280, category: 'Starters', available: false }
  ]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const openForm = (item = null) => {
    setEditingItem(item || { name: '', hindi_name: '', price: '', category: '', available: true });
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Menu Management</h1>
          <p className="mt-1 text-sm text-gray-500">Manage your catalog with AI bilingual tags.</p>
        </div>
        <Button onClick={() => openForm()} className="flex items-center">
          <Plus size={18} className="mr-2" /> Add Item
        </Button>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/[0.06]">
            <thead>
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price (₹)</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-200">{item.name}</div>
                      <div className="text-sm text-gray-500 flex items-center mt-0.5">
                        <Languages size={12} className="mr-1 text-primary-400" />
                        <span>{item.hindi_name || 'Not localized'}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 font-mono">₹{item.price}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{item.category}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant={item.available ? 'success' : 'neutral'}>
                      {item.available ? 'Available' : 'Sold Out'}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => openForm(item)} className="text-primary-400 hover:text-primary-300 mr-4 transition-colors">
                      <Edit2 size={16} />
                    </button>
                    <button className="text-red-400 hover:text-red-300 transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingItem?.id ? 'Edit Item' : 'New Menu Item'}>
        <div className="space-y-4">
          <Input label="Name (English)" value={editingItem?.name} onChange={e => setEditingItem({...editingItem, name: e.target.value})} />
          <Input label="Name (Hindi) 🇮🇳" placeholder="Optional — AI handles translation if blank" value={editingItem?.hindi_name} onChange={e => setEditingItem({...editingItem, hindi_name: e.target.value})} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Price (₹)" type="number" value={editingItem?.price} onChange={e => setEditingItem({...editingItem, price: e.target.value})} />
            <Input label="Category" value={editingItem?.category} onChange={e => setEditingItem({...editingItem, category: e.target.value})} />
          </div>
          <div className="pt-4 flex justify-end space-x-3">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={() => setIsModalOpen(false)}>Save Item</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
