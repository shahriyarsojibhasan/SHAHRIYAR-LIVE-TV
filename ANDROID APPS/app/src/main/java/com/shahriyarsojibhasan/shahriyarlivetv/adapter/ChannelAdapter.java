package com.shahriyarsojibhasan.shahriyarlivetv.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.Glide;
import com.shahriyarsojibhasan.shahriyarlivetv.R;
import com.shahriyarsojibhasan.shahriyarlivetv.model.Channel;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class ChannelAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {
    private static final int TYPE_HEADER = 0;
    private static final int TYPE_CHANNEL = 1;

    private List<Object> items = new ArrayList<>();
    private final OnChannelClickListener listener;
    private String activeChannelUrl = "";

    public interface OnChannelClickListener {
        void onChannelClick(Channel channel);
    }

    public ChannelAdapter(OnChannelClickListener listener) {
        this.listener = listener;
    }

    public void setChannels(List<Channel> channels) {
        List<Object> newItems = new ArrayList<>();
        // Use LinkedHashMap to preserve the order from M3U
        Map<String, List<Channel>> groups = new LinkedHashMap<>();
        for (Channel channel : channels) {
            String group = channel.getGroup();
            if (!groups.containsKey(group)) {
                groups.put(group, new ArrayList<>());
            }
            groups.get(group).add(channel);
        }

        for (Map.Entry<String, List<Channel>> entry : groups.entrySet()) {
            newItems.add(entry.getKey()); // Header
            newItems.addAll(entry.getValue()); // Channels
        }

        DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DiffCallback(this.items, newItems));
        this.items = newItems;
        diffResult.dispatchUpdatesTo(this);
    }

    private static class DiffCallback extends DiffUtil.Callback {
        private final List<Object> oldList;
        private final List<Object> newList;

        public DiffCallback(List<Object> oldList, List<Object> newList) {
            this.oldList = oldList;
            this.newList = newList;
        }

        @Override
        public int getOldListSize() {
            return oldList.size();
        }

        @Override
        public int getNewListSize() {
            return newList.size();
        }

        @Override
        public boolean areItemsTheSame(int oldItemPosition, int newItemPosition) {
            Object oldItem = oldList.get(oldItemPosition);
            Object newItem = newList.get(newItemPosition);

            if (oldItem instanceof String && newItem instanceof String) {
                return oldItem.equals(newItem);
            } else if (oldItem instanceof Channel && newItem instanceof Channel) {
                return ((Channel) oldItem).getId().equals(((Channel) newItem).getId());
            }
            return false;
        }

        @Override
        public boolean areContentsTheSame(int oldItemPosition, int newItemPosition) {
            Object oldItem = oldList.get(oldItemPosition);
            Object newItem = newList.get(newItemPosition);
            return Objects.equals(oldItem, newItem);
        }
    }

    public String getActiveChannelUrl() {
        return activeChannelUrl;
    }

    public void setActiveChannel(String url) {
        this.activeChannelUrl = url;
        notifyDataSetChanged(); // Still need this for selection highlight
    }

    @Override
    public int getItemViewType(int position) {
        return items.get(position) instanceof String ? TYPE_HEADER : TYPE_CHANNEL;
    }

    @NonNull
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        if (viewType == TYPE_HEADER) {
            View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_category, parent, false);
            return new HeaderViewHolder(view);
        } else {
            View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_channel, parent, false);
            return new ChannelViewHolder(view);
        }
    }

    @Override
    public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
        if (holder instanceof HeaderViewHolder) {
            ((HeaderViewHolder) holder).title.setText((String) items.get(position));
        } else if (holder instanceof ChannelViewHolder) {
            Channel channel = (Channel) items.get(position);
            ChannelViewHolder chHolder = (ChannelViewHolder) holder;
            chHolder.name.setText(channel.getName());
            
            Glide.with(chHolder.logo.getContext())
                    .load(channel.getLogo())
                    .placeholder(R.drawable.placeholder_logo)
                    .into(chHolder.logo);

            if (channel.getUrl().equals(activeChannelUrl)) {
                chHolder.itemView.setBackgroundResource(R.drawable.active_channel_bg);
            } else {
                chHolder.itemView.setBackgroundResource(R.drawable.focused_background);
            }

            chHolder.itemView.setOnClickListener(v -> listener.onChannelClick(channel));
        }
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    public Object getItem(int position) {
        return items.get(position);
    }

    static class ChannelViewHolder extends RecyclerView.ViewHolder {
        ImageView logo;
        TextView name;

        ChannelViewHolder(View itemView) {
            super(itemView);
            logo = itemView.findViewById(R.id.channelLogo);
            name = itemView.findViewById(R.id.channelName);
        }
    }

    static class HeaderViewHolder extends RecyclerView.ViewHolder {
        TextView title;

        HeaderViewHolder(View itemView) {
            super(itemView);
            title = itemView.findViewById(R.id.categoryTitle);
        }
    }
}
